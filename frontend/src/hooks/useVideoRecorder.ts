import { useCallback, useEffect, useRef, useState } from 'react';

interface UseVideoRecorderReturn {
  isRecording: boolean;
  recordingTime: number;
  previewStream: MediaStream | null;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<Blob | null>;
  error: string | null;
}

export function useVideoRecorder(): UseVideoRecorderReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [previewStream, setPreviewStream] = useState<MediaStream | null>(null);
  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
      mediaRecorderRef.current?.stream.getTracks().forEach((track) => track.stop());
      previewStream?.getTracks().forEach((track) => track.stop());
    };
  }, [previewStream]);

  const startRecording = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });

      const preferredMimeType = 'video/webm;codecs=vp8,opus';
      const mediaRecorder = MediaRecorder.isTypeSupported(preferredMimeType)
        ? new MediaRecorder(stream, { mimeType: preferredMimeType })
        : new MediaRecorder(stream);

      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      setPreviewStream(stream);

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.start(1000);
      setIsRecording(true);
      setRecordingTime(0);

      timerRef.current = window.setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start video recording');
    }
  }, []);

  const stopRecording = useCallback(async (): Promise<Blob | null> => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') {
        resolve(null);
        return;
      }

      mediaRecorderRef.current.onstop = () => {
        const blobType = chunksRef.current[0]?.type || 'video/webm';
        const blob = new Blob(chunksRef.current, { type: blobType });

        mediaRecorderRef.current?.stream.getTracks().forEach((track) => track.stop());

        if (timerRef.current) {
          clearInterval(timerRef.current);
          timerRef.current = null;
        }

        setIsRecording(false);
        setPreviewStream(null);
        mediaRecorderRef.current = null;
        resolve(blob);
      };

      mediaRecorderRef.current.stop();
    });
  }, []);

  return {
    isRecording,
    recordingTime,
    previewStream,
    startRecording,
    stopRecording,
    error,
  };
}
