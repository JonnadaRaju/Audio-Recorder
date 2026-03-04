import React, { useState, useEffect, useRef, useCallback } from 'react';
import { apiService, RecordingListItem } from '../services/api';
import { useAudioRecorder } from '../hooks/useAudioRecorder';
import './Dashboard.css';

interface DashboardProps {
  onLogout: () => void;
}

export const Dashboard: React.FC<DashboardProps> = ({ onLogout }) => {
  const [recordings, setRecordings] = useState<RecordingListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentlyPlaying, setCurrentlyPlaying] = useState<number | null>(null);
  const [recordingName, setRecordingName] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [assistantQuery, setAssistantQuery] = useState('');
  const [assistantLoading, setAssistantLoading] = useState(false);
  const [assistantError, setAssistantError] = useState<string | null>(null);
  const [assistantHistory, setAssistantHistory] = useState<
    Array<{ query: string; answer: string; steps: Array<{ step: string; tool: string; output_preview: string }> }>
  >([]);

  const {
    isRecording,
    recordingTime,
    startRecording,
    stopRecording,
    error: recorderError
  } = useAudioRecorder();

  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const currentAudioUrlRef = useRef<string | null>(null);

  const stopCurrentPlayback = useCallback((updateState = true) => {
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
      setCurrentlyPlaying(null);
    }
  }, []);

  const fetchRecordings = async () => {
    try {
      const data = await apiService.getRecordings();
      setRecordings(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch recordings');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRecordings();
  }, []);

  useEffect(() => {
    return () => {
      stopCurrentPlayback(false);
    };
  }, [stopCurrentPlayback]);

  const handleRecord = async () => {
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

  const buildRecordingFilename = (name: string): string => {
    const fallback = `recording_${Date.now()}`;
    const trimmed = name.trim();
    const base = trimmed.length > 0 ? trimmed : fallback;
    const sanitized = base
      .replace(/[<>:"/\\|?*\u0000-\u001F]/g, '')
      .replace(/\s+/g, '_')
      .slice(0, 80);
    const safeBase = sanitized || fallback;
    return safeBase.toLowerCase().endsWith('.webm') ? safeBase : `${safeBase}.webm`;
  };

  const uploadRecording = async (blob: Blob, customName: string) => {
    setUploading(true);
    setError(null);

    try {
      const filename = buildRecordingFilename(customName);
      const file = new File([blob], filename, { type: 'audio/webm' });

      await apiService.uploadRecording(file, recordingTime);
      setRecordingName('');
      await fetchRecordings();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload recording');
    } finally {
      setUploading(false);
    }
  };

  const handlePlay = async (recording: RecordingListItem) => {
    if (currentlyPlaying === recording.id) {
      stopCurrentPlayback();
      return;
    }

    setError(null);
    stopCurrentPlayback();

    try {
      const audioUrl = await apiService.getRecordingAudioUrl(recording.id);
      const audio = new Audio(audioUrl);
      audio.onended = () => {
        stopCurrentPlayback();
      };
      await audio.play();
      currentAudioRef.current = audio;
      currentAudioUrlRef.current = audioUrl;
      setCurrentlyPlaying(recording.id);
    } catch (err) {
      stopCurrentPlayback();
      setError(err instanceof Error ? err.message : 'Failed to play recording');
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this recording?')) {
      return;
    }

    try {
      await apiService.deleteRecording(id);
      await fetchRecordings();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete recording');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
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

  const normalizedSearchQuery = searchQuery.trim().toLowerCase();
  const filteredRecordings = normalizedSearchQuery
    ? recordings.filter((recording) =>
        recording.filename.toLowerCase().includes(normalizedSearchQuery)
      )
    : recordings;

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
        <h1>Audio Recorder</h1>
        <button onClick={onLogout} className="logout-btn">Logout</button>
      </header>

      <div className="recorder-section">
        <input
          type="text"
          className="recording-name-input"
          placeholder="Recording name (optional)"
          value={recordingName}
          onChange={(e) => setRecordingName(e.target.value)}
          disabled={isRecording || uploading}
          maxLength={80}
        />
        <button
          className={`record-btn ${isRecording ? 'recording' : ''}`}
          onClick={handleRecord}
          disabled={uploading}
        >
          {isRecording ? 'Stop Recording' : 'Start Recording'}
        </button>
        <div className="recording-name-hint">
          Leave blank to use an automatic filename.
        </div>
        {isRecording && (
          <div className="recording-time">
            {formatDuration(recordingTime)}
          </div>
        )}
        {(uploading || loading) && (
          <div className="loading">{uploading ? 'Uploading...' : 'Loading...'}</div>
        )}
        {(error || recorderError) && (
          <div className="error-message">{error || recorderError}</div>
        )}
      </div>

      <div className="recordings-section">
        <h2>Your Recordings</h2>
        <div className="recordings-toolbar">
          <input
            type="search"
            className="search-input"
            placeholder="Search recordings by name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <span className="search-count">
            {filteredRecordings.length} / {recordings.length}
          </span>
        </div>
        {recordings.length === 0 && !loading ? (
          <p className="no-recordings">No recordings yet. Click "Start Recording" to begin.</p>
        ) : filteredRecordings.length === 0 ? (
          <p className="no-recordings">No recordings match your search.</p>
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
                    className={`play-btn ${currentlyPlaying === recording.id ? 'playing' : ''}`}
                    onClick={() => handlePlay(recording)}
                  >
                    {currentlyPlaying === recording.id ? 'Pause' : 'Play'}
                  </button>
                  <button
                    className="delete-btn"
                    onClick={() => handleDelete(recording.id)}
                  >
                    Delete
                  </button>
                </div>
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
            placeholder="Ask about your recordings..."
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
