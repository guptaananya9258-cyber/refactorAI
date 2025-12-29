// Frontend JavaScript for RefactorIQ
// Sends the pasted code to the backend `/analyze` endpoint and renders results.

const analyzeBtn = document.getElementById('analyzeBtn');
const codeInput = document.getElementById('codeInput');
const status = document.getElementById('status');
const issuesList = document.getElementById('issuesList');
const suggestionsList = document.getElementById('suggestionsList');
const scoreValue = document.getElementById('scoreValue');
const scoreBarFill = document.getElementById('scoreBarFill');

function setLoading(isLoading){
  analyzeBtn.disabled = isLoading;
  status.textContent = isLoading ? 'Analyzing...' : 'Ready';
}

function renderIssues(issues){
  if(!issues || issues.length === 0){
    issuesList.innerHTML = '<div class="issue info">No issues found.</div>';
    return;
  }

  issuesList.innerHTML = '';
  issues.forEach(it => {
    const div = document.createElement('div');
    div.className = 'issue ' + (it.severity || 'info');
    const title = document.createElement('div');
    title.innerHTML = `<strong>${it.type}</strong> — ${it.message.split('\n')[0]}`;
    const meta = document.createElement('div');
    meta.className = 'meta';
    meta.textContent = `Line: ${it.line || 'n/a'} · Severity: ${it.severity || 'info'}`;
    const suggestion = document.createElement('div');
    suggestion.className = 'meta';
    suggestion.textContent = it.suggestion || '';
    div.appendChild(title);
    div.appendChild(meta);
    if(it.suggestion) div.appendChild(suggestion);
    issuesList.appendChild(div);
  });
}

function renderSuggestions(suggestions){
  if(!suggestions || suggestions.length === 0){
    suggestionsList.textContent = 'No suggestions.';
    return;
  }
  suggestionsList.innerHTML = '';
  const ul = document.createElement('ul');
  suggestions.forEach(s => {
    const li = document.createElement('li');
    li.textContent = s.description || s.type || JSON.stringify(s);
    ul.appendChild(li);
  });
  suggestionsList.appendChild(ul);
}

function renderScore(score){
  scoreValue.textContent = (typeof score === 'number') ? `${score}/100` : '—';
  const pct = Math.max(0, Math.min(100, score || 0));
  scoreBarFill.style.width = pct + '%';
}

async function analyzeCode(){
  const code = codeInput.value;
  if(!code || !code.trim()){
    status.textContent = 'Please paste some Python code first.';
    return;
  }

  setLoading(true);

  try{
    const res = await fetch('/analyze', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({code})
    });

    const data = await res.json();

    if(!data.success){
      // Could be syntax error or server error
      issuesList.innerHTML = `<div class="issue error">${data.error || data.syntax_error?.message || 'Analysis failed.'}</div>`;
      renderScore(0);
      suggestionsList.textContent = data.reason || '';
      status.textContent = 'Analysis failed';
    } else {
      renderIssues(data.issues || []);
      renderSuggestions(data.suggestions || []);
      renderScore(data.score);
      status.textContent = 'Analysis complete';
    }

  }catch(err){
    issuesList.innerHTML = `<div class="issue error">Network or server error: ${err.message}</div>`;
    renderScore(0);
    status.textContent = 'Error';
  } finally{
    setLoading(false);
  }
}

analyzeBtn.addEventListener('click', analyzeCode);

// Optional: keyboard shortcut Ctrl+Enter to analyze
codeInput.addEventListener('keydown', (e)=>{
  if((e.ctrlKey || e.metaKey) && e.key === 'Enter') analyzeCode();
});
