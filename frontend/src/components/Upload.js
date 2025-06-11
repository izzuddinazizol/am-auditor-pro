import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { toast } from 'react-toastify';
import api from '../services/api';

const Upload = () => {
  const [isUploading, setIsUploading] = useState(false);
  const navigate = useNavigate();

  const onDrop = async (acceptedFiles) => {
    if (acceptedFiles.length === 0) {
      toast.error('Please select a valid file');
      return;
    }

    const file = acceptedFiles[0];
    
    // Validate file size (100MB limit)
    const maxSize = 100 * 1024 * 1024;
    if (file.size > maxSize) {
      toast.error('File size too large. Maximum size is 100MB.');
      return;
    }

    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await api.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      toast.success('File uploaded successfully!');
      navigate(`/status/${response.data.job_id}`);
    } catch (error) {
      console.error('Upload error:', error);
      console.error('Error details:', error.response?.data);
      console.error('Error status:', error.response?.status);
      
      let errorMessage = 'Upload failed. Please try again.';
      
      if (error.response?.data?.message) {
        errorMessage = error.response.data.message;
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      toast.error(errorMessage);
    } finally {
      setIsUploading(false);
    }
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'audio/*': ['.mp3', '.wav', '.m4a'],
      'video/*': ['.mp4', '.avi', '.mov'],
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
      'image/*': ['.png', '.jpg', '.jpeg']
    },
    multiple: false,
    disabled: isUploading
  });

  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-primary text-text-dark mb-4">
          AI-Powered Conversation Analysis
        </h1>
        <p className="text-xl text-text-secondary mb-8">
          Upload your conversation files and get instant, objective feedback 
          with actionable insights for performance improvement.
        </p>
        
        <div className="flex flex-wrap justify-center gap-4 text-sm text-text-secondary">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 bg-primary rounded-full"></span>
            <span>Audio & Video Files</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 bg-primary rounded-full"></span>
            <span>PDF Documents</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 bg-primary rounded-full"></span>
            <span>Images & Text Files</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 bg-primary rounded-full"></span>
            <span>Multi-language Support</span>
          </div>
        </div>
      </div>

      {/* Upload Section */}
      <div className="card mb-8">
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all duration-200
            ${isDragActive 
              ? 'border-primary bg-primary-50' 
              : 'border-border hover:border-primary hover:bg-bg-accent'
            }
            ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          <input {...getInputProps()} />
          
          <div className="mb-6">
            <svg
              className="mx-auto h-16 w-16 text-text-light"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </div>

          {isUploading ? (
            <div>
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-lg font-accent text-text-dark">Uploading...</p>
              <p className="text-text-secondary">Please wait while we process your file</p>
            </div>
          ) : (
            <div>
              <p className="text-lg font-accent text-text-dark mb-2">
                {isDragActive ? 'Drop your file here' : 'Drop your conversation file here'}
              </p>
              <p className="text-text-secondary mb-4">
                or <span className="text-primary font-accent">click to browse</span>
              </p>
              <p className="text-sm text-text-light">
                Supports MP3, WAV, MP4, PDF, DOCX, TXT, PNG, JPG (max 100MB)
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Features Grid */}
      <div className="grid md:grid-cols-3 gap-6">
        <div className="card text-center">
          <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h3 className="text-lg font-primary text-text-dark mb-2">Lightning Fast</h3>
          <p className="text-text-secondary">
            Get comprehensive analysis results in minutes, not hours of manual review.
          </p>
        </div>

        <div className="card text-center">
          <div className="w-12 h-12 bg-success/10 rounded-lg flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-success" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-lg font-primary text-text-dark mb-2">Objective Scoring</h3>
          <p className="text-text-secondary">
            Consistent, unbiased evaluation based on proven Account Management best practices.
          </p>
        </div>

        <div className="card text-center">
          <div className="w-12 h-12 bg-warning/10 rounded-lg flex items-center justify-center mx-auto mb-4">
            <svg className="w-6 h-6 text-warning" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
          </div>
          <h3 className="text-lg font-primary text-text-dark mb-2">Actionable Insights</h3>
          <p className="text-text-secondary">
            Receive specific improvement recommendations and coaching guidance.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Upload; 