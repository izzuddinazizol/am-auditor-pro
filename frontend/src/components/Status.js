import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../services/api';

const Status = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!jobId) return;

    const checkStatus = async () => {
      try {
        const response = await api.get(`/api/status/${jobId}`);
        const statusData = response.data;
        setStatus(statusData);

        // If completed, redirect to results
        if (statusData.status === 'completed') {
          setTimeout(() => {
            navigate(`/results/${jobId}`);
          }, 1000);
        }
        
        // If failed, show error
        if (statusData.status === 'failed') {
          toast.error(statusData.error || 'Processing failed');
        }
      } catch (error) {
        toast.error('Failed to get status. Please try again.');
        console.error('Status check error:', error);
      } finally {
        setLoading(false);
      }
    };

    // Initial check
    checkStatus();

    // Poll every 2 seconds if not completed
    const interval = setInterval(() => {
      if (status?.status === 'completed' || status?.status === 'failed') {
        clearInterval(interval);
        return;
      }
      checkStatus();
    }, 2000);

    return () => clearInterval(interval);
  }, [jobId, navigate, status?.status]);

  const getStatusColor = (statusType) => {
    switch (statusType) {
      case 'uploaded':
        return 'text-blue-600';
      case 'processing':
        return 'text-yellow-600';
      case 'transcribing':
        return 'text-orange-600';
      case 'analyzing':
        return 'text-purple-600';
      case 'completed':
        return 'text-green-600';
      case 'failed':
        return 'text-red-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusIcon = (statusType) => {
    switch (statusType) {
      case 'completed':
        return (
          <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        );
      case 'failed':
        return (
          <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        );
      default:
        return (
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary-600"></div>
        );
    }
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="card text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-lg font-medium text-gray-900">Loading status...</p>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="card text-center">
          <svg className="w-12 h-12 text-red-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Job Not Found</h2>
          <p className="text-gray-600 mb-4">The requested job could not be found.</p>
          <button 
            onClick={() => navigate('/')}
            className="btn-primary"
          >
            Upload New File
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="card">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">Processing Status</h1>
          <p className="text-gray-600">Job ID: {jobId}</p>
        </div>

        {/* Progress Bar */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm font-medium text-gray-700">Progress</span>
            <span className="text-sm font-medium text-gray-700">{status.progress}%</span>
          </div>
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${status.progress}%` }}
            ></div>
          </div>
        </div>

        {/* Status Display */}
        <div className="flex items-center justify-center space-x-4 mb-8">
          {getStatusIcon(status.status)}
          <div className="text-center">
            <p className={`text-lg font-semibold capitalize ${getStatusColor(status.status)}`}>
              {status.status.replace('_', ' ')}
            </p>
            <p className="text-gray-600">{status.message}</p>
          </div>
        </div>

        {/* Processing Steps */}
        <div className="space-y-4">
          <div className={`flex items-center space-x-3 ${status.progress >= 10 ? 'text-green-600' : 'text-gray-400'}`}>
            <div className={`w-3 h-3 rounded-full ${status.progress >= 10 ? 'bg-green-600' : 'bg-gray-300'}`}></div>
            <span>File uploaded and validated</span>
          </div>
          
          <div className={`flex items-center space-x-3 ${status.progress >= 30 ? 'text-green-600' : status.progress >= 10 ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className={`w-3 h-3 rounded-full ${status.progress >= 30 ? 'bg-green-600' : status.progress >= 10 ? 'bg-blue-600' : 'bg-gray-300'}`}></div>
            <span>Extracting transcript from file</span>
          </div>
          
          <div className={`flex items-center space-x-3 ${status.progress >= 70 ? 'text-green-600' : status.progress >= 30 ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className={`w-3 h-3 rounded-full ${status.progress >= 70 ? 'bg-green-600' : status.progress >= 30 ? 'bg-blue-600' : 'bg-gray-300'}`}></div>
            <span>Analyzing conversation with AI</span>
          </div>
          
          <div className={`flex items-center space-x-3 ${status.progress >= 100 ? 'text-green-600' : status.progress >= 70 ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className={`w-3 h-3 rounded-full ${status.progress >= 100 ? 'bg-green-600' : status.progress >= 70 ? 'bg-blue-600' : 'bg-gray-300'}`}></div>
            <span>Generating detailed report</span>
          </div>
        </div>

        {/* Actions */}
        <div className="mt-8 flex justify-center space-x-4">
          {status.status === 'completed' && (
            <button 
              onClick={() => navigate(`/results/${jobId}`)}
              className="btn-primary"
            >
              View Results
            </button>
          )}
          
          {status.status === 'failed' && (
            <button 
              onClick={() => navigate('/')}
              className="btn-primary"
            >
              Try Again
            </button>
          )}
          
          <button 
            onClick={() => navigate('/')}
            className="btn-secondary"
          >
            Upload New File
          </button>
        </div>

        {/* Error Display */}
        {status.error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="flex items-start space-x-3">
              <svg className="w-5 h-5 text-red-500 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h3 className="text-sm font-medium text-red-800">Processing Error</h3>
                <p className="text-sm text-red-700 mt-1">{status.error}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Status; 