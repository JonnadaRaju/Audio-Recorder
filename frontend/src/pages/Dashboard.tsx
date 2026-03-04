import React, { useState, useEffect, useRef } from 'react';
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

  const {
    isRecording,
    recordingTime,
    startRecording,
    stopRecording,
    error: recorderError
  } = useAudioRecorder();
  
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);

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

  const handleRecord = async () => {
    if (isRecording) {
      const blob = await stopRecording();
      if (blob) {
        await uploadRecording(blob);
      }
    } else {
      await startRecording();
    }
  };

  const uploadRecording = async (blob: Blob) => {
    setUploading(true);
    setError(null);
    
    try {
      const filename = `recording_${Date.now()}.webm`;
      const file = new File([blob], filename, { type: 'audio/webm' });
      
      await apiService.uploadRecording(file, recordingTime);
      await fetchRecordings();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to upload recording');
    } finally {
      setUploading(false);
    }
  };

  const handlePlay = (recording: RecordingListItem) => {
    if (currentlyPlaying === recording.id) {
      currentAudioRef.current?.pause();
      setCurrentlyPlaying(null);
    } else {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
      const audio = new Audio(apiService.getStreamUrl(recording.id));
      audio.onended = () => {
        setCurrentlyPlaying(null);
        currentAudioRef.current = null;
      };
      audio.play();
      currentAudioRef.current = audio;
      setCurrentlyPlaying(recording.id);
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

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Audio Recorder</h1>
        <button onClick={onLogout} className="logout-btn">Logout</button>
      </header>

      <div className="recorder-section">
        <button
          className={`record-btn ${isRecording ? 'recording' : ''}`}
          onClick={handleRecord}
          disabled={uploading}
        >
          {isRecording ? 'Stop Recording' : 'Start Recording'}
        </button>
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
        {recordings.length === 0 && !loading ? (
          <p className="no-recordings">No recordings yet. Click "Start Recording" to begin.</p>
        ) : (
          <div className="recordings-list">
            {recordings.map((recording) => (
              <div key={recording.id} className="recording-item">
                <div className="recording-info">
                  <span className="filename">{recording.filename}</span>
                  <span className="metadata">
                    {formatDate(recording.created_at)} • {formatFileSize(recording.file_size)} • {formatDuration(recording.duration)}
                  </span>
                </div>
                <div className="recording-actions">
                  <button
                    className={`play-btn ${currentlyPlaying === recording.id ? 'playing' : ''}`}
                    onClick={() => handlePlay(recording)}
                  >
                    {currentlyPlaying === recording.id ? '⏸' : '▶'}
                  </button>
                  <button
                    className="delete-btn"
                    onClick={() => handleDelete(recording.id)}
                  >
                    🗑
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
