import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Play, Download, RefreshCw, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import './App.css';

interface TestRun {
  run_id: string;
  mode: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  started_at?: string;
  duration_seconds?: number;
  results_summary?: { passed: number; failed: number; skipped: number };
}

const API_BASE = process.env.REACT_APP_API_URL || 'https://api.sanlamconnect.com/qa-portal';
const POLL_INTERVAL = 5000; // 5 seconds

export default function App() {
  const [mode, setMode] = useState('mock');
  const [selectedSuites, setSelectedSuites] = useState<string[]>([]);
  const [isExecuting, setIsExecuting] = useState(false);
  const [currentRun, setCurrentRun] = useState<TestRun | null>(null);
  const [history, setHistory] = useState<TestRun[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const [activeTab, setActiveTab] = useState('execute');

  const suites = [
    'CloudWatch Alarms',
    'Financial Calculator',
    'Dashboard Refresh',
    'Scheduled Reports',
    'Exception Monitoring',
    'Self-Healing',
    'Alarm Notifications',
    'Data Consistency'
  ];

  // Load history on mount
  useEffect(() => {
    loadHistory();
  }, []);

  // Poll for results if test running
  useEffect(() => {
    if (!currentRun || currentRun.status !== 'running') return;

    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_BASE}/test/${currentRun.run_id}/status`);
        setCurrentRun(response.data);

        // Load logs
        const logsResponse = await axios.get(`${API_BASE}/test/${currentRun.run_id}/logs`);
        setLogs(logsResponse.data.logs);
      } catch (error) {
        console.error('Failed to poll status:', error);
      }
    }, POLL_INTERVAL);

    return () => clearInterval(interval);
  }, [currentRun]);

  const loadHistory = async () => {
    try {
      const response = await axios.get(`${API_BASE}/test/history?limit=10`);
      setHistory(response.data.runs);
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  };

  const handleExecute = async () => {
    setIsExecuting(true);

    try {
      const response = await axios.post(`${API_BASE}/test/execute`, {
        mode,
        suites: selectedSuites.length > 0 ? selectedSuites : undefined
      });

      setCurrentRun(response.data);
      setLogs([]);
      setActiveTab('results');
      loadHistory();
    } catch (error: any) {
      alert(`Failed to execute tests: ${error.response?.data?.error || error.message}`);
    } finally {
      setIsExecuting(false);
    }
  };

  const handleGenerateReport = async (format: 'html' | 'pdf') => {
    if (!currentRun) return;

    try {
      const response = await axios.post(`${API_BASE}/report/generate`, {
        run_id: currentRun.run_id,
        format
      });

      // Download report
      window.location.href = response.data.url;
    } catch (error: any) {
      alert(`Failed to generate report: ${error.message}`);
    }
  };

  const toggleSuite = (suite: string) => {
    setSelectedSuites(prev =>
      prev.includes(suite) ? prev.filter(s => s !== suite) : [...prev, suite]
    );
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <AlertCircle className="w-5 h-5 text-gray-500" />;
      case 'running':
        return <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900">QA Portal</h1>
          <p className="text-gray-600">Financial Impact Integration Test Dashboard</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left: Test Configuration */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold mb-4">Test Configuration</h2>

              {/* Mode Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Mode
                </label>
                <div className="space-y-2">
                  {['dry-run', 'mock', 'live'].map(m => (
                    <label key={m} className="flex items-center">
                      <input
                        type="radio"
                        value={m}
                        checked={mode === m}
                        onChange={e => setMode(e.target.value)}
                        className="rounded border-gray-300"
                      />
                      <span className="ml-2 text-sm text-gray-700 capitalize">{m}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Suite Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Test Suites
                </label>
                <div className="space-y-2">
                  {suites.map(suite => (
                    <label key={suite} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={selectedSuites.includes(suite)}
                        onChange={() => toggleSuite(suite)}
                        className="rounded border-gray-300"
                      />
                      <span className="ml-2 text-sm text-gray-700">{suite}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Execute Button */}
              <button
                onClick={handleExecute}
                disabled={isExecuting || (mode === 'live' && selectedSuites.length === 0)}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-bold py-2 px-4 rounded flex items-center justify-center gap-2"
              >
                <Play size={18} />
                Execute Tests
              </button>
            </div>
          </div>

          {/* Right: Results & History */}
          <div className="lg:col-span-2">
            {/* Tabs */}
            <div className="flex gap-4 mb-6">
              <button
                onClick={() => setActiveTab('results')}
                className={`px-4 py-2 font-medium ${
                  activeTab === 'results'
                    ? 'border-b-2 border-blue-600 text-blue-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Results
              </button>
              <button
                onClick={() => setActiveTab('history')}
                className={`px-4 py-2 font-medium ${
                  activeTab === 'history'
                    ? 'border-b-2 border-blue-600 text-blue-600'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                History
              </button>
            </div>

            {/* Results Tab */}
            {activeTab === 'results' && (
              <div className="bg-white rounded-lg shadow p-6">
                {currentRun ? (
                  <>
                    <div className="mb-6">
                      <div className="flex items-center gap-3 mb-4">
                        {getStatusIcon(currentRun.status)}
                        <div>
                          <h3 className="text-lg font-bold">{currentRun.run_id}</h3>
                          <p className="text-sm text-gray-600 capitalize">{currentRun.status}</p>
                        </div>
                      </div>

                      {/* Results Summary */}
                      {currentRun.results_summary && (
                        <div className="grid grid-cols-3 gap-4 mb-4">
                          <div className="bg-green-50 p-3 rounded">
                            <div className="text-2xl font-bold text-green-600">
                              {currentRun.results_summary.passed}
                            </div>
                            <div className="text-sm text-gray-600">Passed</div>
                          </div>
                          <div className="bg-red-50 p-3 rounded">
                            <div className="text-2xl font-bold text-red-600">
                              {currentRun.results_summary.failed}
                            </div>
                            <div className="text-sm text-gray-600">Failed</div>
                          </div>
                          <div className="bg-yellow-50 p-3 rounded">
                            <div className="text-2xl font-bold text-yellow-600">
                              {currentRun.results_summary.skipped}
                            </div>
                            <div className="text-sm text-gray-600">Skipped</div>
                          </div>
                        </div>
                      )}

                      {/* Report Buttons */}
                      {currentRun.status === 'completed' && (
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleGenerateReport('html')}
                            className="flex-1 bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded flex items-center justify-center gap-2"
                          >
                            <Download size={18} />
                            HTML Report
                          </button>
                          <button
                            onClick={() => handleGenerateReport('pdf')}
                            className="flex-1 bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded flex items-center justify-center gap-2"
                          >
                            <Download size={18} />
                            PDF Report
                          </button>
                        </div>
                      )}
                    </div>

                    {/* Logs */}
                    <div className="border-t pt-4">
                      <h4 className="font-bold mb-2">Logs ({logs.length})</h4>
                      <div className="bg-gray-800 text-gray-100 p-3 rounded text-sm font-mono max-h-64 overflow-y-auto">
                        {logs.length > 0 ? (
                          logs.map((log, i) => <div key={i}>{log}</div>)
                        ) : (
                          <div className="text-gray-500">No logs yet...</div>
                        )}
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="text-center text-gray-500 py-8">
                    <Clock size={48} className="mx-auto mb-2 opacity-50" />
                    <p>No test execution yet</p>
                  </div>
                )}
              </div>
            )}

            {/* History Tab */}
            {activeTab === 'history' && (
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="font-bold mb-4">Recent Test Runs</h3>
                <div className="space-y-2">
                  {history.length > 0 ? (
                    history.map(run => (
                      <div
                        key={run.run_id}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded hover:bg-gray-100 cursor-pointer"
                        onClick={() => {
                          setCurrentRun(run);
                          setActiveTab('results');
                        }}
                      >
                        <div className="flex items-center gap-3 flex-1">
                          {getStatusIcon(run.status)}
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              {run.mode} - {run.created_at}
                            </p>
                            <p className="text-xs text-gray-600 capitalize">{run.status}</p>
                          </div>
                        </div>
                        {run.duration_seconds && (
                          <div className="text-sm text-gray-600">{run.duration_seconds}s</div>
                        )}
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-500 text-center py-4">No history yet</p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
