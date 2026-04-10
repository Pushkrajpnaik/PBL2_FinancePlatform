import React, { useState, useEffect } from 'react';
import { riskAPI } from '../services/api';
import toast from 'react-hot-toast';
import { Shield, CheckCircle } from 'lucide-react';

export default function RiskProfile() {
  const [questions, setQuestions] = useState<any[]>([]);
  const [answers, setAnswers] = useState<any>({});
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [saved, setSaved] = useState<any>(null);

  useEffect(() => {
    // Load questionnaire
    riskAPI.getQuestionnaire()
      .then(r => {
        console.log('Questionnaire data:', r.data);
        if (r.data && r.data.questions) {
          setQuestions(r.data.questions);
        }
      })
      .catch(err => console.error('Failed to load questionnaire:', err));

    // Try to load saved profile — 404 is OK
    riskAPI.getMyProfile()
      .then(r => setSaved(r.data))
      .catch(() => null);
  }, []);

  const handleSubmit = async () => {
    if (Object.keys(answers).length < 10) {
      toast.error('Please answer all 10 questions');
      return;
    }
    setLoading(true);
    try {
      const res = await riskAPI.assess(answers);
      setResult(res.data);
      setSaved(res.data);
      toast.success('Risk profile assessed!');
    } catch (err: any) {
      toast.error('Assessment failed');
    } finally {
      setLoading(false);
    }
  };

  const profileColors: any = {
    Conservative: 'text-blue-400',
    Moderate: 'text-yellow-400',
    Aggressive: 'text-red-400',
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="font-display font-bold flex items-center gap-2" style={{ fontSize: 28, color: 'var(--text-primary)', letterSpacing: '-0.02em' }}>
            <Shield className="text-blue-500" /> Risk Profile Assessment
        </h1>
        <p className="text-slate-400 mt-1">Answer 10 questions to get your personalized risk profile</p>
      </div>

      {saved && !result && (
        <div className="card border border-blue-500/30">
          <h3 className="font-semibold text-white mb-2">Your Current Profile</h3>
          <div className="flex items-center gap-4">
            <div>
              <p className={`text-3xl font-bold ${profileColors[saved.profile_type]}`}>{saved.profile_type}</p>
              <p className="text-slate-400 text-sm">Score: {saved.score}/100</p>
            </div>
            <p className="text-slate-300 text-sm flex-1">{saved.description}</p>
          </div>
        </div>
      )}

      {result && (
        <div className="card border border-green-500/30 bg-green-500/5">
          <div className="flex items-center gap-2 mb-4">
            <CheckCircle className="text-green-400" size={20} />
            <h3 className="font-semibold text-white">Assessment Complete!</h3>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-slate-400 text-sm">Your Profile</p>
              <p className={`text-3xl font-bold ${profileColors[result.profile_type]}`}>{result.profile_type}</p>
              <p className="text-slate-400 text-sm mt-1">Score: {result.score}/100</p>
            </div>
            <div>
              <p className="text-slate-400 text-sm mb-2">Recommended Allocation</p>
              {Object.entries(result.recommended_allocation).map(([k, v]: any) => (
                <div key={k} className="flex justify-between text-sm mb-1">
                  <span className="text-slate-300 capitalize">{k.replace(/_/g, ' ')}</span>
                  <span className="text-white font-medium">{v}%</span>
                </div>
              ))}
            </div>
          </div>
          <p className="text-slate-400 text-sm mt-4">{result.description}</p>
        </div>
      )}

      {questions.length === 0 && (
        <div className="card">
          <p className="text-slate-400 animate-pulse">Loading questionnaire...</p>
        </div>
      )}

      {questions.length > 0 && (
        <div className="space-y-4">
          {questions.map((q: any, i: number) => (
            <div key={q.id} className="card">
              <p className="text-white font-medium mb-3">{i + 1}. {q.question}</p>
              <div className="space-y-2">
                {Object.entries(q.options).map(([val, label]: any) => (
                  <button
                    key={val}
                    onClick={() => setAnswers({ ...answers, [q.id]: parseInt(val) })}
                    className={`w-full text-left px-4 py-2 rounded-lg text-sm transition-all ${
                      answers[q.id] === parseInt(val)
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                    }`}
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>
          ))}
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="btn-primary w-full py-3 text-lg"
          >
            {loading ? 'Analyzing...' : `Submit Assessment (${Object.keys(answers).length}/10)`}
          </button>
        </div>
      )}
    </div>
  );
}