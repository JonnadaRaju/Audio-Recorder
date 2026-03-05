import React, { useCallback, useEffect, useRef, useState } from 'react';
import { apiService, RecordingListItem, VideoListItem } from '../services/api';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import { useVideoRecorder } from '../hooks/useVideoRecorder';
import './Dashboard.css';

interface DashboardProps {
  onLogout: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onLogout }) => {
  const [recordings, setRecordings] = useState<RecordingListItem[]>([]);
  const [videos, setVideos] = useState<VideoListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploadingAudio, setUploadingAudio] = useState(false);
  const [uploadingVideo, setUploadingVideo] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [currentlyPlayingAudio, setCurrentlyPlayingAudio] = useState<number | null>(null);
  const [currentlyPlayingVideo, setCurrentlyPlayingVideo] = useState<number | null>(null);
  const [currentlyPlayingVideoUrl, setCurrentlyPlayingVideoUrl] = useState<string | null>(null);

  const [recordingName, setRecordingName] = useState('');
  const [videoName, setVideoName] = useState('');

  const [searchQuery, setSearchQuery] = useState('');
  const [videoSearchQuery, setVideoSearchQuery] = useState('');

  const [assistantQuery, setAssistantQuery] = useState('');
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [assistantError, setAssistantError] = useState<string | null>(null);
  const [assistantHistory, setAssistantHistory] = useState<
    Array<{ query: string; answer: string; steps: Array<{ step: string; tool: string; output_preview: string }> }>
  >([]);

  const [pendingVideoBlob, setPendingVideoBlob] = useState<Blob | null>(null);
  const [pendingVideoPreviewUrl, setPendingVideoPreviewUrl] = useState<string | null>(null);

  const {
    isRecording,
    recordingTime,
    startRecording,
    stopRecording,
    error: recorderError,
  } = useAudioRecorder();

  const {
    isRecording: isVideoRecording,
    recordingTime: videoRecordingTime,
    previewStream,
    startRecording: startVideoRecording,
    stopRecording: stopVideoRecording,
    error: videoRecorderError,
  } = useVideoRecorder();

  const liveVideoPreviewRef = useRef<HTMLVideoElement | null>(null);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const currentAudioUrlRef = useRef<string | null>(null);
  const currentVideoUrlRef = useRef<string | null>(null);

  const stopCurrentAudioPlayback = useCallback((updateState = true) => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.onended = null;
      currentAudioRef.current = null;
    }
    if (currentAudioUrlRef.current) {
      URL.revokeObjectURL(currentAudioUrlRef.current);
      currentAudioUrlRef.current = null;
    }
    if (updateState) {
      setCurrentlyPlayingAudio(null);
    }
  }, []);

  const stopCurrentVideoPlayback = useCallback((updateState = true) => {
    if (currentVideoUrlRef.current) {
      URL.revokeObjectURL(currentVideoUrlRef.current);
      currentVideoUrlRef.current = null;
    }
    if (updateState) {
      setCurrentlyPlayingVideo(null);
      setCurrentlyPlayingVideoUrl(null);
    }
  }, []);

  const fetchMediaLibrary = async () => {
    try {
      const [audioData, videoData] = await Promise.all([
        apiService.getRecordings(),
        apiService.getVideos(),
      ]);
      setRecordings(audioData);
      setVideos(videoData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch media library');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMediaLibrary();
  }, []);

  useEffect(() => {
    return () => {
      stopCurrentAudioPlayback(false);
      stopCurrentVideoPlayback(false);
    };
  }, [stopCurrentAudioPlayback, stopCurrentVideoPlayback]);

  useEffect(() => {
    const videoEl = liveVideoPreviewRef.current;
    if (!videoEl) {
      return;
    }

    videoEl.srcObject = previewStream;

    if (previewStream) {
      const playPromise = videoEl.play();
      if (playPromise) {
        playPromise.catch(() => {
          // Ignore autoplay interruption errors; user interaction already started recording.
        });
      }
    }
  }, [previewStream]);

  useEffect(() => {
    if (!pendingVideoBlob) {
      setPendingVideoPreviewUrl(null);
      return;
    }

    const url = URL.createObjectURL(pendingVideoBlob);
    setPendingVideoPreviewUrl(url);

    return () => {
      URL.revokeObjectURL(url);
    };
  }, [pendingVideoBlob]);

  const buildFilename = (name: string, defaultPrefix: string, extension: string): string => {
    const fallback = `${defaultPrefix}_${Date.now()}`;
    const trimmed = name.trim();
    const base = trimmed.length > 0 ? trimmed : fallback;
    const sanitized = base
      .replace(/[<>:"/\\|?*]/g, '')
      .replace(/[\r\n\t]/g, ' ')
      .replace(/\s+/g, '_')
      .slice(0, 80);
    const safeBase = sanitized || fallback;
    return safeBase.toLowerCase().endsWith(extension) ? safeBase : `${safeBase}${extension}`;
  };

  const uploadRecording = async (blob: Blob, customName: string) => {
    setUploadingAudio(true);
    setError(null);

    try {
      const filename = buildFilename(customName, 'recording', '.webm');
      const file = new File([blob], filename, { type: 'audio/webm' });
      await apiService.uploadRecording(file, recordingTime);
      setRecordingName('');
      await fetchMediaLibrary();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload recording');
    } finally {
      setUploadingAudio(false);
    }
  };

  const handleAudioRecord = async () => {
    if (isRecording) {
      const nameAtStop = recordingName;
      const blob = await stopRecording();
      if (blob) {
        await uploadRecording(blob, nameAtStop);
      }
    } else {
      await startRecording();
    }
  };

  const handleStartVideo = async () => {
    setPendingVideoBlob(null);
    setError(null);
    await startVideoRecording();
  };

  const uploadVideoBlob = async (blob: Blob, customName: string, durationSeconds?: number): Promise<boolean> => {
    setUploadingVideo(true);
    setError(null);

    try {
      const filename = buildFilename(customName, 'video', '.webm');
      const fileType = blob.type || 'video/webm';
      const file = new File([blob], filename, { type: fileType });
      await apiService.uploadVideo(file, durationSeconds || undefined);
      setVideoName('');
      await fetchMediaLibrary();
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload video');
      return false;
    } finally {
      setUploadingVideo(false);
    }
  };

  const handleStopVideo = async () => {
    const nameAtStop = videoName;
    const durationAtStop = videoRecordingTime;
    const blob = await stopVideoRecording();
    if (!blob) {
      return;
    }

    setPendingVideoBlob(blob);
    const uploaded = await uploadVideoBlob(blob, nameAtStop, durationAtStop);
    if (uploaded) {
      setPendingVideoBlob(null);
    }
  };

  const handleUploadVideo = async () => {
    if (!pendingVideoBlob) {
      return;
    }

    const uploaded = await uploadVideoBlob(pendingVideoBlob, videoName, videoRecordingTime);
    if (uploaded) {
      setPendingVideoBlob(null);
    }
  };

  const handlePlayAudio = async (recording: RecordingListItem) => {
    if (currentlyPlayingAudio === recording.id) {
      stopCurrentAudioPlayback();
      return;
    }

    setError(null);
    stopCurrentAudioPlayback();

    try {
      const audioUrl = await apiService.getRecordingAudioUrl(recording.id);
      const audio = new Audio(audioUrl);
      audio.onended = () => {
        stopCurrentAudioPlayback();
      };
      await audio.play();
      currentAudioRef.current = audio;
      currentAudioUrlRef.current = audioUrl;
      setCurrentlyPlayingAudio(recording.id);
    } catch (err) {
      stopCurrentAudioPlayback();
      setError(err instanceof Error ? err.message : 'Failed to play recording');
    }
  };

  const handlePlayVideo = async (video: VideoListItem) => {
    if (currentlyPlayingVideo === video.id) {
      stopCurrentVideoPlayback();
      return;
    }

    setError(null);
    stopCurrentVideoPlayback();

    try {
      const videoUrl = await apiService.getVideoStreamUrl(video.id);
      currentVideoUrlRef.current = videoUrl;
      setCurrentlyPlayingVideo(video.id);
      setCurrentlyPlayingVideoUrl(videoUrl);
    } catch (err) {
      stopCurrentVideoPlayback();
      setError(err instanceof Error ? err.message : 'Failed to play video');
    }
  };

  const handleDeleteAudio = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this recording?')) {
      return;
    }

    try {
      await apiService.deleteRecording(id);
      if (currentlyPlayingAudio === id) {
        stopCurrentAudioPlayback();
      }
      await fetchMediaLibrary();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete recording');
    }
  };

  const handleDeleteVideo = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this video?')) {
      return;
    }

    try {
      await apiService.deleteVideo(id);
      if (currentlyPlayingVideo === id) {
        stopCurrentVideoPlayback();
      }
      await fetchMediaLibrary();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete video');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDuration = (seconds: number | null): string => {
    if (!seconds) return '--:--';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleString();
  };

  const normalizedAudioSearch = searchQuery.trim().toLowerCase();
  const filteredRecordings = normalizedAudioSearch
    ? recordings.filter((recording) => recording.filename.toLowerCase().includes(normalizedAudioSearch))
    : recordings;

  const normalizedVideoSearch = videoSearchQuery.trim().toLowerCase();
  const filteredVideos = normalizedVideoSearch
    ? videos.filter((video) => video.filename.toLowerCase().includes(normalizedVideoSearch))
    : videos;

  const handleAskAssistant = async (e: React.FormEvent) => {
    e.preventDefault();
    const question = assistantQuery.trim();
    if (!question) {
      return;
    }

    setAssistantLoading(true);
    setAssistantError(null);
    try {
      const response = await apiService.askAgent(question);
      setAssistantHistory((prev) => [
        {
          query: question,
          answer: response.answer,
          steps: response.steps.map((step) => ({
            step: step.step,
            tool: step.tool,
            output_preview: step.output_preview,
          })),
        },
        ...prev,
      ]);
      setAssistantQuery('');
    } catch (err) {
      setAssistantError(err instanceof Error ? err.message : 'Failed to query assistant');
    } finally {
      setAssistantLoading(false);
    }
  };

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Media Recorder</h1>
        <button onClick={onLogout} className="logout-btn">Logout</button>
      </header>

      <div className="recorder-section">
        <h2>Audio Recording</h2>
        <input
          type="text"
          className="recording-name-input"
          placeholder="Audio filename (optional)"
          value={recordingName}
          onChange={(e) => setRecordingName(e.target.value)}
          disabled={isRecording || uploadingAudio}
          maxLength={80}
        />
        <button
          className={`record-btn ${isRecording ? 'recording' : ''}`}
          onClick={handleAudioRecord}
          disabled={uploadingAudio}
        >
          {isRecording ? 'Stop Audio Recording' : 'Start Audio Recording'}
        </button>
        <div className="recording-name-hint">
          Audio recording uploads automatically when you stop.
        </div>
        {isRecording && <div className="recording-time">{formatDuration(recordingTime)}</div>}
      </div>

      <div className="recorder-section video-recorder-section">
        <h2>Video Recording</h2>
        <input
          type="text"
          className="recording-name-input"
          placeholder="Video filename (optional)"
          value={videoName}
          onChange={(e) => setVideoName(e.target.value)}
          disabled={isVideoRecording || uploadingVideo}
          maxLength={80}
        />

        <div className="video-record-controls">
          <button className="record-btn" onClick={handleStartVideo} disabled={isVideoRecording || uploadingVideo}>
            Start Recording
          </button>
          <button className="record-btn recording" onClick={handleStopVideo} disabled={!isVideoRecording}>
            Stop Recording
          </button>
          <button className="assistant-btn" onClick={handleUploadVideo} disabled={!pendingVideoBlob || isVideoRecording || uploadingVideo}>
            {uploadingVideo ? 'Uploading...' : 'Upload'}
          </button>
        </div>
        <div className="recording-name-hint">
          Video uploads automatically when you stop. Use Upload only to retry a failed upload.
        </div>

        {isVideoRecording && <div className="recording-time">{formatDuration(videoRecordingTime)}</div>}

        {isVideoRecording && (
          <video ref={liveVideoPreviewRef} className="video-preview" autoPlay muted playsInline />
        )}

        {!isVideoRecording && pendingVideoPreviewUrl && (
          <video className="video-preview" controls src={pendingVideoPreviewUrl} />
        )}
      </div>

      {(uploadingAudio || uploadingVideo || loading) && (
        <div className="loading">
          {uploadingAudio ? 'Uploading audio...' : uploadingVideo ? 'Uploading video...' : 'Loading media...'}
        </div>
      )}
      {(error || recorderError || videoRecorderError) && (
        <div className="error-message">{error || recorderError || videoRecorderError}</div>
      )}

      <div className="recordings-section">
        <h2>Your Audio Recordings</h2>
        <div className="recordings-toolbar">
          <input
            type="search"
            className="search-input"
            placeholder="Search audio by filename..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <span className="search-count">{filteredRecordings.length} / {recordings.length}</span>
        </div>

        {recordings.length === 0 && !loading ? (
          <p className="no-recordings">No audio recordings yet.</p>
        ) : filteredRecordings.length === 0 ? (
          <p className="no-recordings">No audio recordings match your search.</p>
        ) : (
          <div className="recordings-list">
            {filteredRecordings.map((recording) => (
              <div key={recording.id} className="recording-item">
                <div className="recording-info">
                  <span className="filename">{recording.filename}</span>
                  <span className="metadata">
                    {formatDate(recording.created_at)} | {formatFileSize(recording.file_size)} | {formatDuration(recording.duration)}
                  </span>
                </div>
                <div className="recording-actions">
                  <button
                    className={`play-btn ${currentlyPlayingAudio === recording.id ? 'playing' : ''}`}
                    onClick={() => handlePlayAudio(recording)}
                  >
                    {currentlyPlayingAudio === recording.id ? 'Pause' : 'Play'}
                  </button>
                  <button className="delete-btn" onClick={() => handleDeleteAudio(recording.id)}>
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="recordings-section">
        <h2>Your Videos</h2>
        <div className="recordings-toolbar">
          <input
            type="search"
            className="search-input"
            placeholder="Search videos by filename..."
            value={videoSearchQuery}
            onChange={(e) => setVideoSearchQuery(e.target.value)}
          />
          <span className="search-count">{filteredVideos.length} / {videos.length}</span>
        </div>

        {videos.length === 0 && !loading ? (
          <p className="no-recordings">No videos yet.</p>
        ) : filteredVideos.length === 0 ? (
          <p className="no-recordings">No videos match your search.</p>
        ) : (
          <div className="recordings-list">
            {filteredVideos.map((video) => (
              <div key={video.id} className="recording-item video-item">
                <div className="recording-info">
                  <span className="filename">{video.filename}</span>
                  <span className="metadata">
                    {formatDate(video.created_at)} | {formatFileSize(video.file_size)} | {formatDuration(video.duration)}
                  </span>
                  {video.summary && <span className="metadata">Summary: {video.summary}</span>}
                </div>
                <div className="recording-actions">
                  <button
                    className={`play-btn ${currentlyPlayingVideo === video.id ? 'playing' : ''}`}
                    onClick={() => handlePlayVideo(video)}
                  >
                    {currentlyPlayingVideo === video.id ? 'Hide' : 'Play'}
                  </button>
                  <button className="delete-btn" onClick={() => handleDeleteVideo(video.id)}>
                    Delete
                  </button>
                </div>

                {currentlyPlayingVideo === video.id && currentlyPlayingVideoUrl && (
                  <video className="video-player" controls autoPlay src={currentlyPlayingVideoUrl} />
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="assistant-section">
        <h2>AI Assistant</h2>
        <form className="assistant-form" onSubmit={handleAskAssistant}>
          <input
            type="text"
            className="assistant-input"
            placeholder="Ask about your audio and video recordings..."
            value={assistantQuery}
            onChange={(e) => setAssistantQuery(e.target.value)}
            disabled={assistantLoading}
          />
          <button className="assistant-btn" type="submit" disabled={assistantLoading}>
            {assistantLoading ? 'Thinking...' : 'Ask'}
          </button>
        </form>

        {assistantError && <div className="error-message">{assistantError}</div>}
        {assistantHistory.length === 0 ? (
          <p className="no-recordings">No assistant queries yet.</p>
        ) : (
          <div className="assistant-history">
            {assistantHistory.map((item, idx) => (
              <div key={`${item.query}-${idx}`} className="assistant-item">
                <p className="assistant-query"><strong>Q:</strong> {item.query}</p>
                <p className="assistant-answer"><strong>A:</strong> {item.answer}</p>
                <div className="assistant-steps">
                  {item.steps.map((step) => (
                    <div key={`${idx}-${step.step}-${step.tool}`} className="assistant-step">
                      <span className="assistant-step-tool">{step.tool}</span>
                      <span className="assistant-step-preview">{step.output_preview}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
