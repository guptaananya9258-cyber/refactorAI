import React, { useState } from 'react'
import axios from 'axios'

function App(){
  const [code, setCode] = useState("# Paste Python code here\n")
  const [problem, setProblem] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [copyStatus, setCopyStatus] = useState('')

  const demoExample = `# Example: Two-sum (DSA)
def two_sum(nums, target):
    for i in range(len(nums)):
        for j in range(i+1, len(nums)):
            if nums[i] + nums[j] == target:
                return [i, j]
    return None

# Problem: Find indices of two numbers that add up to target
`;

  async function analyze(){
    setLoading(true)
    setResult(null)
    try{
      const res = await axios.post('/api/analyze', {code, problem, language: 'python'})
      setResult(res.data)
    }catch(e){
      setResult({error: e.message})
    }finally{
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen p-8">
      <header className="mb-6">
        <h1 className="text-3xl font-semibold">RefactorAI</h1>
        <p className="text-gray-600">From errors to expert-level solutions.</p>
      </header>

      <div className="grid md:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-xl font-medium mb-2">Code Input</h2>
          <label className="text-sm text-gray-500">Problem / Description</label>
          <textarea value={problem} onChange={e=>setProblem(e.target.value)} className="w-full p-2 border rounded mb-3" rows={2} />
          <label className="text-sm text-gray-500">Python Code</label>
          <textarea value={code} onChange={e=>setCode(e.target.value)} className="w-full p-3 border rounded font-mono h-56" />
          <div className="flex gap-2 mt-3">
            <button className="btn" onClick={analyze} disabled={loading}>{loading? 'Analyzing...' : 'Analyze'}</button>
            <button className="px-4 py-2 border rounded" onClick={()=>{setCode(''); setProblem(''); setResult(null); setCopyStatus('')}}>Reset</button>
            <button className="px-4 py-2 border rounded" onClick={()=>{setCode(demoExample); setProblem('Demo: implement Two-sum (find indices)'); setResult(null)}}>Load Example</button>
          </div>
        </div>

        <div>
          <div className="card mb-4">
            <h3 className="text-lg font-medium">Error Analysis</h3>
            <div className="mt-2">
              {result ? (
                result.paused ? (
                  <div className="text-red-600">Analysis paused until code is syntactically valid.<pre className="text-sm bg-red-50 p-2 rounded mt-2">{JSON.stringify(result.syntax_error, null, 2)}</pre></div>
                ) : (
                  <div>
                    <pre className="text-sm bg-red-50 p-2 rounded text-red-700">{JSON.stringify(result.analysis?.issues || [], null, 2)}</pre>
                  </div>
                )
              ) : (<div className="text-gray-500">No analysis yet.</div>)}
            </div>
          </div>

          <div className="card mb-4">
            <h3 className="text-lg font-medium">Corrected Solution</h3>
            <div className="mt-2">
              {result && !result.paused ? (
                <pre className="text-sm bg-green-50 p-2 rounded text-green-800">{result.fixed_code || result.raw || '—'}</pre>
              ) : <div className="text-gray-500">—</div>}
            </div>
            <div className="flex gap-2 mt-3 items-center">
              <button
                className="px-3 py-1 bg-green-600 text-white rounded"
                onClick={async ()=>{
                  const text = result?.fixed_code || result?.raw || '';
                  if(!text) return;
                  await navigator.clipboard.writeText(text);
                  setCopyStatus('Copied!');
                  setTimeout(()=>setCopyStatus(''),2000);
                }}
              >Copy Code</button>
              <span className="text-sm text-green-700">{copyStatus}</span>
            </div>
          </div>

          <div className="card">
            <h3 className="text-lg font-medium">Explanation</h3>
            <div className="mt-2 text-sm text-gray-700">
              {result && !result.paused ? (
                result.from_ai ? (<pre>{JSON.stringify(result, null, 2)}</pre>) : (<pre>{JSON.stringify(result.analysis, null, 2)}</pre>)
              ) : <div className="text-gray-500">—</div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
