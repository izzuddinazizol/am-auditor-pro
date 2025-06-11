import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../services/api';

const Results = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showRubric, setShowRubric] = useState(false);
  const [rubricContent, setRubricContent] = useState(null);

  useEffect(() => {
    const fetchResults = async () => {
      try {
        const response = await api.get(`/api/results/${jobId}`);
        setResults(response.data);
      } catch (error) {
        toast.error('Failed to load results. Please try again.');
        console.error('Results fetch error:', error);
      } finally {
        setLoading(false);
      }
    };

    if (jobId) {
      fetchResults();
    }
  }, [jobId]);

  // Download functionality
  const downloadResults = (format) => {
    if (!results) return;
    
    const { summary, scored_items, participant_info, coaching_summary } = results;
    const timestamp = new Date().toLocaleString();
    const filename = `AM_Auditor_Analysis_${new Date().toISOString().slice(0, 10)}`;
    
    // Helper function to create content for all formats
    const createContent = () => {
      const participantSection = `CONVERSATION PARTICIPANTS
Business Name: ${participant_info?.business_name || 'Not identified'}
Customer Name: ${participant_info?.customer_name || 'Not identified'}
Agent Name: ${participant_info?.agent_name || 'Not identified'}

`;
      
      const summarySection = `ANALYSIS SUMMARY
Subject: ${summary?.subject || 'N/A'}
Type: ${summary?.conversation_type || 'N/A'}
Overall Score: ${summary?.total_score || 0}%
Pass Status: ${summary?.pass_status ? 'PASS' : 'FAIL'}

KEY STRENGTHS:
${(summary?.key_strengths || []).map(strength => `• ${strength}`).join('\n')}

AREAS FOR IMPROVEMENT:
${(summary?.areas_for_improvement || []).map(area => `• ${area}`).join('\n')}

ACTION PLAN:
${(summary?.action_plan || []).map(action => `• ${action}`).join('\n')}

`;

      const scoredItemsSection = `DETAILED SCORE BREAKDOWN:
${(scored_items || []).map(item => 
`${item.category} - ${item.item}
Score: ${item.score}/5
Justification: ${item.justification}
Evidence: ${(item.evidence || []).join('; ')}
${item.improvement_guidance ? `Improvement Guidance: ${item.improvement_guidance}` : ''}
`).join('\n')}

`;

      const coachingSection = `ELITE COACHING ASSESSMENT:
${coaching_summary || 'No coaching summary available'}

Generated on: ${timestamp}`;

      return participantSection + summarySection + scoredItemsSection + coachingSection;
    };

    if (format === 'txt') {
      const content = createContent();
      const blob = new Blob([content], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } 
    else if (format === 'json') {
      const jsonData = {
        analysis_results: results,
        generated_at: timestamp,
        export_format: 'json'
      };
      const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
    else if (format === 'csv') {
      const csvData = [
        ['Category', 'Item', 'Score', 'Justification', 'Evidence', 'Improvement Guidance'],
        ...(scored_items || []).map(item => [
          item.category,
          item.item,
          item.score,
          item.justification,
          (item.evidence || []).join('; '),
          item.improvement_guidance || ''
        ])
      ];
      
      const csvContent = csvData.map(row => 
        row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')
      ).join('\n');
      
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${filename}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
    else if (format === 'pdf') {
      // Create a formatted HTML content for PDF conversion
      const content = createContent();
      const htmlContent = `
        <!DOCTYPE html>
        <html>
        <head>
          <title>AM Auditor Pro Analysis Report</title>
          <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            h1 { color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px; }
            h2 { color: #1f2937; margin-top: 30px; }
            .participant-info { background: #f3f4f6; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            .score { font-size: 18px; font-weight: bold; color: #059669; }
            .section { margin-bottom: 25px; }
            .item { margin-bottom: 15px; padding: 10px; border-left: 4px solid #e5e7eb; }
            pre { white-space: pre-wrap; word-wrap: break-word; }
          </style>
        </head>
        <body>
          <h1>AM Auditor Pro - Conversation Analysis Report</h1>
          <pre>${content}</pre>
        </body>
        </html>
      `;
      
      // Open in new window for printing to PDF
      const printWindow = window.open('', '_blank');
      printWindow.document.write(htmlContent);
      printWindow.document.close();
      printWindow.focus();
      
      // Trigger print dialog after content loads
      setTimeout(() => {
        printWindow.print();
      }, 500);
    }
    
    toast.success(`Analysis downloaded as ${format.toUpperCase()}`);
  };

  // Fetch rubric content when needed
  const fetchRubricContent = async () => {
    if (rubricContent) return; // Already loaded
    
    try {
      setLoading(true);
      const response = await api.get('/api/rubric');
      setRubricContent(response.data.rubric || 'No rubric content available');
    } catch (error) {
      console.error('Error fetching rubric:', error);
      setRubricContent('Unable to load rubric content');
      toast.error('Failed to load rubric content');
    } finally {
      setLoading(false);
    }
  };

  // Handle rubric toggle
  const handleRubricToggle = () => {
    setShowRubric(!showRubric);
    if (!showRubric && !rubricContent) {
      fetchRubricContent();
    }
  };



  if (loading) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-lg font-accent text-text-dark">Loading results...</p>
        </div>
      </div>
    );
  }

  if (!results) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="card text-center">
          <h2 className="text-xl font-primary text-text-dark mb-2">Results Not Found</h2>
          <p className="text-text-secondary mb-4">The results for this job could not be found.</p>
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

  const { summary, scored_items, participant_info, coaching_summary } = results;
  const percentage = summary.total_score || 0;

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-3xl font-primary text-text-dark">AM Auditor Pro - Analysis Results</h1>
            <p className="text-text-secondary">File: {results.filename}</p>
          </div>
          <button 
            onClick={() => navigate('/')}
            className="btn-secondary"
          >
            Upload New File
          </button>
        </div>
        
        {/* Enhanced Participant Information */}
        <div className="mt-6 p-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
          <h3 className="text-lg font-primary text-text-dark mb-4 flex items-center">
            <span className="w-3 h-3 bg-blue-500 rounded-full mr-2"></span>
            Conversation Participants
          </h3>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="bg-white p-4 rounded-lg shadow-sm border border-blue-100">
              <p className="text-sm font-accent text-blue-600 mb-1">Business Name</p>
              <p className="text-lg text-text-dark font-primary">
                {participant_info?.business_name || 'Not identified'}
              </p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm border border-blue-100">
              <p className="text-sm font-accent text-blue-600 mb-1">Customer Name</p>
              <p className="text-lg text-text-dark font-primary">
                {participant_info?.customer_name || 'Not identified'}
              </p>
            </div>
            <div className="bg-white p-4 rounded-lg shadow-sm border border-blue-100">
              <p className="text-sm font-accent text-blue-600 mb-1">Agent Name</p>
              <p className="text-lg text-text-dark font-primary">
                {participant_info?.agent_name || 'Not identified'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 1. Identified Conversation Type */}
      <div className="card">
        <h2 className="text-xl font-primary text-text-dark mb-4">1. Identified Conversation Type</h2>
        <div className="bg-primary-50 p-4 rounded-lg">
          <p className="text-lg text-text-primary">
            <strong>Identified Conversation Type:</strong> 
            <span className="ml-2 inline-flex px-3 py-1 rounded-full text-sm font-accent bg-primary text-white">
              {summary.conversation_type === 'consultation' ? 'Consultation' : 
               summary.conversation_type === 'service' ? 'Servicing' : 
               'Mixed - Consultation & Servicing'}
            </span>
          </p>
          <p className="text-sm text-text-secondary mt-2">
            {summary.conversation_type === 'consultation' ? 'New client discussions, sales presentations, solution exploration' : 
             summary.conversation_type === 'service' ? 'Existing client support, issue resolution, account maintenance' : 
             'Combination of both consultation and servicing elements'}
          </p>
        </div>
      </div>

      {/* 2. Conversation Subject */}
      <div className="card">
        <h2 className="text-xl font-primary text-text-dark mb-4">2. Conversation Subject</h2>
        <p className="text-lg text-text-primary">
          <strong>Conversation Subject:</strong> {summary.subject}
        </p>
      </div>

      {/* 3. Total Score & Pass/Fail Status */}
      <div className="card">
        <h2 className="text-xl font-primary text-text-dark mb-6">3. Total Score & Pass/Fail Status</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="text-center">
            <div className="text-5xl font-primary text-primary mb-4">{percentage}%</div>
            <div className={`inline-flex items-center px-4 py-2 rounded-full text-lg font-accent ${
              summary.pass_status 
                ? 'badge-success' 
                : 'badge-danger'
            }`}>
              <strong>Status: {summary.pass_status ? 'Pass' : 'Fail'}</strong>
            </div>
            <p className="text-sm text-text-secondary mt-2">
              (Passing mark is 80%)
            </p>
          </div>
          <div className="space-y-2">
            <p className="text-text-primary">
              <strong>Calculation Method:</strong> Average of all applicable scored items (1-5 scale)
            </p>
            <p className="text-text-primary">
              <strong>Items Scored:</strong> {scored_items?.length || 0}
            </p>
            <p className="text-text-primary">
              <strong>Processing Time:</strong> {results.processing_time?.toFixed(1)}s
            </p>
            <p className="text-text-primary">
              <strong>Analysis Date:</strong> {new Date(results.created_at).toLocaleDateString()}
            </p>
          </div>
        </div>
      </div>

      {/* 4. Summarized Feedback and Action Plan */}
      <div className="card">
        <h2 className="text-xl font-primary text-text-dark mb-6">4. Elite Coaching Assessment & Action Plan for AM</h2>
        
        {/* Elite Coaching Summary */}
        {coaching_summary && (
          <div className="mb-6">
            <h3 className="text-lg font-accent text-text-dark mb-3 flex items-center">
              <span className="w-3 h-3 bg-primary rounded-full mr-2"></span>
              Elite Performance Coaching by Marcus Chen
            </h3>
            <div className="bg-gradient-to-r from-primary-50 to-primary-100 p-6 rounded-lg border-l-4 border-primary">
              <div className="text-text-primary whitespace-pre-line">
                {coaching_summary}
              </div>
            </div>
          </div>
        )}
        
        {/* Overall Summary - Fallback if no coaching summary */}
        {!coaching_summary && (
          <div className="mb-6">
            <h3 className="text-lg font-accent text-text-dark mb-3">Overall Summary</h3>
            <p className="text-text-primary bg-bg-secondary p-4 rounded-lg">
              The AM demonstrated a {percentage >= 80 ? 'strong' : percentage >= 60 ? 'moderate' : 'developing'} level of performance 
              in this {summary.conversation_type?.toLowerCase()?.replace('_', ' ')} conversation focused on {summary.subject?.toLowerCase()}. 
              {percentage >= 80 
                ? 'The interaction met professional standards with effective communication and service delivery.'
                : 'There are several areas requiring improvement to reach optimal performance standards.'
              }
            </p>
          </div>
        )}

        {/* Key Strengths */}
        <div className="mb-6">
          <h3 className="text-lg font-accent text-text-dark mb-3">Key Strengths</h3>
          <ul className="space-y-2">
            {summary.key_strengths?.map((strength, index) => (
              <li key={index} className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-success rounded-full mt-2 flex-shrink-0"></div>
                <span className="text-text-primary">{strength}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Primary Areas for Improvement */}
        <div className="mb-6">
          <h3 className="text-lg font-accent text-text-dark mb-3">Primary Areas for Improvement</h3>
          <ul className="space-y-2">
            {summary.areas_for_improvement?.map((area, index) => (
              <li key={index} className="flex items-start space-x-3">
                <div className="w-2 h-2 bg-warning rounded-full mt-2 flex-shrink-0"></div>
                <span className="text-text-primary">{area}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Action Plan */}
        <div>
          <h3 className="text-lg font-accent text-text-dark mb-3">Action Plan</h3>
          <ol className="space-y-3">
            {summary.action_plan?.map((action, index) => (
              <li key={index} className="flex items-start space-x-3">
                <span className="flex-shrink-0 w-8 h-8 bg-primary-100 text-primary rounded-full flex items-center justify-center text-sm font-primary">
                  {index + 1}
                </span>
                <span className="text-text-primary">{action}</span>
              </li>
            ))}
          </ol>
        </div>
      </div>

      {/* 5. Enhanced Detailed Score Breakdown and Improvement Guidance */}
      <div className="card">
        <h2 className="text-xl font-primary text-text-dark mb-6">5. Detailed Score Breakdown and Improvement Guidance</h2>
        
        {/* Helper function to group scored items by category */}
        {(() => {
          // Group items by category
          const groupedItems = (scored_items || []).reduce((groups, item) => {
            const category = item.category || 'Other';
            if (!groups[category]) {
              groups[category] = [];
            }
            groups[category].push(item);
            return groups;
          }, {});

          // Define category order and styling - handle both numbered and non-numbered formats
          const categoryConfig = {
            // Without numbers (current API format)
            'Core Communication Fundamentals': {
              title: 'Core Communication Fundamentals',
              color: 'bg-blue-50 border-blue-200',
              headerColor: 'bg-blue-100',
              icon: '💬'
            },
            'Consultation & Pitching Focus': {
              title: 'Consultation & Pitching Focus', 
              color: 'bg-green-50 border-green-200',
              headerColor: 'bg-green-100',
              icon: '🎯'
            },
            'Servicing Focus': {
              title: 'Servicing Focus',
              color: 'bg-purple-50 border-purple-200', 
              headerColor: 'bg-purple-100',
              icon: '🛠️'
            },
            // With numbers (fallback for backend format)
            '1. Core Communication Fundamentals': {
              title: 'Core Communication Fundamentals',
              color: 'bg-blue-50 border-blue-200',
              headerColor: 'bg-blue-100',
              icon: '💬'
            },
            '2. Consultation & Pitching Focus': {
              title: 'Consultation & Pitching Focus', 
              color: 'bg-green-50 border-green-200',
              headerColor: 'bg-green-100',
              icon: '🎯'
            },
            '3. Servicing Focus': {
              title: 'Servicing Focus',
              color: 'bg-purple-50 border-purple-200', 
              headerColor: 'bg-purple-100',
              icon: '🛠️'
            },
            'Business Development Focus': {
              title: 'Business Development Focus',
              color: 'bg-orange-50 border-orange-200',
              headerColor: 'bg-orange-100',
              icon: '💼'
            }
          };

          // Define preferred category order (prioritize non-numbered format)
          const preferredCategoryOrder = [
            'Core Communication Fundamentals',
            'Consultation & Pitching Focus', 
            'Servicing Focus',
            'Business Development Focus',
            '1. Core Communication Fundamentals',
            '2. Consultation & Pitching Focus',
            '3. Servicing Focus'
          ];
          
          const otherCategories = Object.keys(groupedItems).filter(cat => !preferredCategoryOrder.includes(cat));

          return [...preferredCategoryOrder, ...otherCategories].map(categoryKey => {
            const items = groupedItems[categoryKey];
            if (!items || items.length === 0) return null;

            const config = categoryConfig[categoryKey] || {
              title: categoryKey,
              color: 'bg-gray-50 border-gray-200',
              headerColor: 'bg-gray-100', 
              icon: '📋'
            };

            return (
              <div key={categoryKey} className={`mb-8 border rounded-lg overflow-hidden ${config.color}`}>
                {/* Category Header */}
                <div className={`${config.headerColor} px-6 py-4 border-b`}>
                  <h3 className="text-lg font-primary text-text-dark flex items-center">
                    <span className="mr-3 text-xl">{config.icon}</span>
                    {config.title}
                    <span className="ml-3 px-2 py-1 bg-white rounded-full text-sm text-text-secondary">
                      {items.length} item{items.length !== 1 ? 's' : ''}
                    </span>
                  </h3>
                </div>

                {/* Enhanced Category Table with improved layout */}
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200 bg-white/50">
                        <th className="text-left py-3 px-4 font-primary text-text-dark w-1/6">Behavior/Skill</th>
                        <th className="text-center py-3 px-4 font-primary text-text-dark w-16">Score</th>
                        <th className="text-left py-3 px-4 font-primary text-text-dark w-1/4">Justification</th>
                        <th className="text-left py-3 px-4 font-primary text-text-dark w-1/4">Improvement Guidance</th>
                        <th className="text-left py-3 px-4 font-primary text-text-dark w-1/6">Evidence</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((item, index) => (
                        <tr key={index} className={`border-b border-gray-100 ${item.score < 4 ? 'bg-warning/5' : 'bg-success/5'} hover:bg-white/80 transition-colors`}>
                          <td className="py-4 px-4 text-sm font-accent text-text-dark align-top">
                            {item.item}
                          </td>
                          <td className="py-4 px-4 text-center align-top">
                            <span className={`inline-flex items-center justify-center w-10 h-10 rounded-full text-sm font-primary ${
                              item.score >= 4 ? 'bg-success text-white' : 
                              item.score >= 3 ? 'bg-warning text-white' : 
                              'bg-danger text-white'
                            }`}>
                              {item.score}
                            </span>
                          </td>
                          <td className="py-4 px-4 text-text-primary text-base align-top">
                            <div className="leading-relaxed">
                              {item.justification}
                            </div>
                          </td>
                          <td className="py-4 px-4 text-text-primary text-base align-top">
                            {item.score < 4 ? (
                              <div className="bg-orange-50 border border-orange-200 p-4 rounded-lg">
                                <div className="text-orange-800 leading-relaxed">
                                  {item.improvement_guidance}
                                </div>
                              </div>
                            ) : (
                              <div className="flex items-center text-success font-accent text-base">
                                <span className="w-2 h-2 bg-success rounded-full mr-2"></span>
                                Meets/Exceeds Expectations
                              </div>
                            )}
                          </td>
                          <td className="py-4 px-4 text-text-primary text-sm align-top">
                            {item.evidence && item.evidence.length > 0 ? (
                              <div className="space-y-1">
                                {Array.isArray(item.evidence) ? item.evidence.map((quote, idx) => (
                                  <div key={idx} className="bg-white p-2 rounded text-xs italic border-l-2 border-primary/20">
                                    "{quote}"
                                  </div>
                                )) : (
                                  <div className="bg-white p-2 rounded text-xs italic border-l-2 border-primary/20">
                                    "{item.evidence}"
                                  </div>
                                )}
                              </div>
                            ) : (
                              <span className="text-text-light italic text-xs">No specific evidence provided</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            );
          }).filter(Boolean);
        })()}
        
        {/* View Original Rubric Button */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <button
            onClick={handleRubricToggle}
            className="inline-flex items-center px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors duration-200 shadow-sm"
          >
            <span className="mr-2">📋</span>
            {showRubric ? 'Hide Original Rubric' : 'View Original Rubric'}
          </button>
        </div>

        {/* Original Rubric Display */}
        {showRubric && (
          <div className="mt-6 p-6 bg-gray-50 border border-gray-200 rounded-lg">
            <h4 className="text-lg font-primary text-text-dark mb-4 flex items-center">
              <span className="mr-2">📋</span>
              Original Scoring Rubric
            </h4>
            <div className="bg-white p-4 rounded border text-sm text-text-primary leading-relaxed whitespace-pre-line">
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                  <span className="ml-3 text-text-secondary">Loading rubric...</span>
                </div>
              ) : rubricContent ? (
                rubricContent
              ) : (
                <div className="text-text-secondary italic">
                  Unable to load original rubric content.
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Download Results Section */}
      <div className="card bg-gradient-to-r from-gray-50 to-gray-100 border border-gray-200">
        <h3 className="text-lg font-primary text-text-dark mb-4 flex items-center">
          <span className="w-3 h-3 bg-gray-500 rounded-full mr-2"></span>
          Download Analysis Results
        </h3>
        <p className="text-text-secondary mb-4">
          Download your complete conversation analysis in various formats for record-keeping and sharing.
        </p>
        <div className="flex flex-wrap gap-4">
          <button
            onClick={() => downloadResults('pdf')}
            className="bg-red-600 hover:bg-red-700 text-white px-6 py-3 rounded-lg font-accent transition-colors duration-200 flex items-center space-x-2"
          >
            <span>📋</span>
            <span>Download as PDF</span>
          </button>
          <button
            onClick={() => downloadResults('doc')}
            className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-accent transition-colors duration-200 flex items-center space-x-2"
          >
            <span>📄</span>
            <span>Download as DOC</span>
          </button>
          <button
            onClick={() => downloadResults('docx')}
            className="bg-green-600 hover:bg-green-700 text-white px-6 py-3 rounded-lg font-accent transition-colors duration-200 flex items-center space-x-2"
          >
            <span>📑</span>
            <span>Download as DOCX</span>
          </button>
          <button
            onClick={() => downloadResults('txt')}
            className="bg-gray-600 hover:bg-gray-700 text-white px-6 py-3 rounded-lg font-accent transition-colors duration-200 flex items-center space-x-2"
          >
            <span>📝</span>
            <span>Download as TXT</span>
          </button>
        </div>
        <div className="mt-4 text-sm text-text-secondary">
          <p><strong>PDF:</strong> Professional formatted report with full styling (recommended)</p>
          <p><strong>DOC/DOCX:</strong> Microsoft Word compatible format for editing and sharing</p>
          <p><strong>TXT:</strong> Plain text format for universal compatibility</p>
        </div>
      </div>

      {/* Additional Information */}
      <div className="card bg-bg-accent">
        <h3 className="text-lg font-primary text-text-dark mb-4">Analysis Information</h3>
        <div className="grid md:grid-cols-2 gap-4 text-sm text-text-secondary">
          <div>
            <p><strong>Analysis Engine:</strong> AM Auditor Pro v1.0</p>
            <p><strong>Rubric Version:</strong> Dynamic Conversation Audit Scorecard</p>
          </div>
          <div>
            <p><strong>Job ID:</strong> {jobId}</p>
            <p><strong>Report Generated:</strong> {new Date().toLocaleString()}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Results; 