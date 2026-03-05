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
  const previewStreamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<number | null>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current !== null) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const stopStream = useCallback((stream: MediaStream | null) => {
    stream?.getTracks().forEach((track) => track.stop());
  }, []);

  const cleanupRecordingState = useCallback(() => {
    clearTimer();
    setIsRecording(false);
    setPreviewStream(null);
    previewStreamRef.current = null;
    mediaRecorderRef.current = null;
  }, [clearTimer]);

  useEffect(() => {
    return () => {
      clearTimer();
      stopStream(mediaRecorderRef.current?.stream ?? null);
      stopStream(previewStreamRef.current);
    };
  }, [clearTimer, stopStream]);

  const startRecording = useCallback(async () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      return;
    }

    try {
      setError(null);

      stopStream(previewStreamRef.current);
      previewStreamRef.current = null;
      setPreviewStream(null);

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: true });

      const preferredMimeType = 'video/webm;codecs=vp8,opus';
      const mediaRecorder = MediaRecorder.isTypeSupported(preferredMimeType)
        ? new MediaRecorder(stream, { mimeType: preferredMimeType })
        : new MediaRecorder(stream);

      mediaRecorderRef.current = mediaRecorder;
      previewStreamRef.current = stream;
      chunksRef.current = [];
      setPreviewStream(stream);

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      // Keep UI state consistent even if recording ends due permissions/device changes.
      mediaRecorder.onstop = () => {
        stopStream(stream);
        cleanupRecordingState();
      };

      mediaRecorder.start(1000);
      setIsRecording(true);
      setRecordingTime(0);

      clearTimer();
      timerRef.current = window.setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start video recording');
      cleanupRecordingState();
    }
  }, [clearTimer, cleanupRecordingState, stopStream]);

  const stopRecording = useCallback(async (): Promise<Blob | null> => {
    return new Promise((resolve) => {
      const recorder = mediaRecorderRef.current;
      if (!recorder) {
        cleanupRecordingState();
        resolve(null);
        return;
      }

      const finalize = () => {
        const hasChunks = chunksRef.current.length > 0;
        const blobType = chunksRef.current[0]?.type || 'video/webm';
        const blob = hasChunks ? new Blob(chunksRef.current, { type: blobType }) : null;

        stopStream(recorder.stream);
        cleanupRecordingState();
        resolve(blob);
      };

      if (recorder.state === 'inactive') {
        finalize();
        return;
      }

      const originalOnStop = recorder.onstop;
      recorder.onstop = () => {
        originalOnStop?.call(recorder, new Event('stop'));
        finalize();
      };

      // Flush any buffered media before stopping so short recordings still produce a blob.
      try {
        recorder.requestData();
      } catch {
        // Safe no-op when recorder cannot flush buffered data in current state.
      }

      recorder.stop();
    });
  }, [cleanupRecordingState, stopStream]);

  return {
    isRecording,
    recordingTime,
    previewStream,
    startRecording,
    stopRecording,
    error,
  };
}
