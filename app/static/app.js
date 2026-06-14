async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, options);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Request failed');
        }
        
        return data;
    } catch (error) {
        throw error;
    }
}

function showLoading(button) {
    button.disabled = true;
    button.querySelector('.btn-text').style.display = 'none';
    button.querySelector('.loader').style.display = 'block';
}

function hideLoading(button) {
    button.disabled = false;
    button.querySelector('.btn-text').style.display = 'inline';
    button.querySelector('.loader').style.display = 'none';
}

function showMessage(elementId, message, type) {
    const element = document.getElementById(elementId);
    element.textContent = message;
    element.className = `message ${type}`;
    element.style.display = 'block';
    
    setTimeout(() => {
        element.style.display = 'none';
    }, 5000);
}

async function loadSpeakers() {
    const container = document.getElementById('speakersTable');
    
    try {
        const speakers = await apiRequest('/speakers');
        
        if (speakers.length === 0) {
            container.innerHTML = '<p class="loading">No speakers enrolled yet</p>';
            updateSpeakerDropdown([]);
            return;
        }
        
        let tableHtml = `
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Enrolled At</th>
                        <th>Action</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        speakers.forEach(speaker => {
            const date = new Date(speaker.created_at).toLocaleString();
            tableHtml += `
                <tr>
                    <td>${speaker.name}</td>
                    <td>${date}</td>
                    <td>
                        <button class="btn btn-danger" onclick="deleteSpeaker('${speaker.name}')">Delete</button>
                    </td>
                </tr>
            `;
        });
        
        tableHtml += '</tbody></table>';
        container.innerHTML = tableHtml;
        
        updateSpeakerDropdown(speakers);
        
    } catch (error) {
        container.innerHTML = `<p class="message error">Failed to load speakers: ${error.message}</p>`;
    }
}

function updateSpeakerDropdown(speakers) {
    const dropdown = document.getElementById('verifySpeaker');
    if (!dropdown) return;
    
    dropdown.innerHTML = '<option value="">-- Select a speaker --</option>';
    
    speakers.forEach(speaker => {
        const option = document.createElement('option');
        option.value = speaker.name;
        option.textContent = speaker.name;
        dropdown.appendChild(option);
    });
}

async function deleteSpeaker(name) {
    if (!confirm(`Are you sure you want to delete speaker "${name}"?`)) {
        return;
    }
    
    try {
        await apiRequest(`/speakers/${name}`, { method: 'DELETE' });
        showMessage('enrollMessage', `Speaker "${name}" deleted successfully`, 'success');
        loadSpeakers();
    } catch (error) {
        showMessage('enrollMessage', `Failed to delete speaker: ${error.message}`, 'error');
    }
}

if (document.getElementById('enrollForm')) {
    document.getElementById('enrollForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const button = e.target.querySelector('button[type="submit"]');
        const name = document.getElementById('enrollName').value;
        const files = document.getElementById('enrollFiles').files;
        
        if (files.length === 0) {
            showMessage('enrollMessage', 'Please select at least one audio file', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('name', name);
        
        for (let file of files) {
            formData.append('files', file);
        }
        
        showLoading(button);
        
        try {
            const result = await apiRequest('/enroll', {
                method: 'POST',
                body: formData
            });
            
            showMessage('enrollMessage', result.message, 'success');
            e.target.reset();
            loadSpeakers();
        } catch (error) {
            showMessage('enrollMessage', error.message, 'error');
        } finally {
            hideLoading(button);
        }
    });
}

if (document.getElementById('verifyForm')) {
    document.getElementById('verifyForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const button = e.target.querySelector('button[type="submit"]');
        const name = document.getElementById('verifySpeaker').value;
        const file = document.getElementById('verifyFile').files[0];
        
        if (!name) {
            alert('Please select a speaker');
            return;
        }
        
        if (!file) {
            alert('Please select an audio file');
            return;
        }
        
        const formData = new FormData();
        formData.append('name', name);
        formData.append('file', file);
        
        showLoading(button);
        
        const resultDiv = document.getElementById('verifyResult');
        resultDiv.innerHTML = '';
        resultDiv.className = 'result';
        
        try {
            const result = await apiRequest('/verify', {
                method: 'POST',
                body: formData
            });
            
            const similarity = result.similarity;
            const verified = result.verified;
            const threshold = result.threshold;
            
            const percentage = (similarity * 100).toFixed(1);
            
            resultDiv.innerHTML = `
                <div class="similarity-score">${percentage}%</div>
                <div class="progress-bar">
                    <div class="progress-fill ${verified ? 'verified' : 'not-verified'}" 
                         style="width: ${percentage}%"></div>
                </div>
                <div class="verification-status ${verified ? 'verified' : 'not-verified'}">
                    ${verified ? '✓ VERIFIED' : '✗ NOT VERIFIED'}
                </div>
                <p style="margin-top: 1rem; color: #718096;">
                    Threshold: ${(threshold * 100).toFixed(0)}% | Similarity: ${percentage}%
                </p>
            `;
            
            resultDiv.className = 'result show';
            
        } catch (error) {
            resultDiv.innerHTML = `<p class="message error">${error.message}</p>`;
            resultDiv.className = 'result show';
        } finally {
            hideLoading(button);
        }
    });
}

if (document.getElementById('deepfakeForm')) {
    document.getElementById('deepfakeForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const button = e.target.querySelector('button[type="submit"]');
        const file = document.getElementById('deepfakeFile').files[0];
        
        if (!file) {
            alert('Please select an audio file');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        showLoading(button);
        
        const resultDiv = document.getElementById('deepfakeResult');
        resultDiv.innerHTML = '';
        resultDiv.className = 'result';
        
        try {
            const result = await apiRequest('/detect-deepfake', {
                method: 'POST',
                body: formData
            });
            
            const label = result.label;
            const confidence = (result.confidence * 100).toFixed(1);
            const explanation = result.explanation;
            
            resultDiv.innerHTML = `
                <div class="deepfake-badge ${label.toLowerCase()}">${label.toUpperCase()}</div>
                <div class="confidence">Confidence: ${confidence}%</div>
                <div class="explanation">${explanation}</div>
            `;
            
            resultDiv.className = 'result show';
            
        } catch (error) {
            resultDiv.innerHTML = `<p class="message error">${error.message}</p>`;
            resultDiv.className = 'result show';
        } finally {
            hideLoading(button);
        }
    });
}

if (document.getElementById('refreshBtn')) {
    document.getElementById('refreshBtn').addEventListener('click', loadSpeakers);
}

if (document.getElementById('speakersTable')) {
    loadSpeakers();
}

let kycName = '';
let verificationResult = null;
let deepfakeResult = null;

if (document.getElementById('kycEnrollForm')) {
    document.getElementById('kycEnrollForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const button = e.target.querySelector('button[type="submit"]');
        const name = document.getElementById('kycName').value;
        const files = document.getElementById('kycEnrollFiles').files;
        
        if (files.length < 3) {
            showMessage('step1Message', 'Please upload at least 3 audio files', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('name', name);
        
        for (let file of files) {
            formData.append('files', file);
        }
        
        showLoading(button);
        
        try {
            const result = await apiRequest('/enroll', {
                method: 'POST',
                body: formData
            });
            
            kycName = name;
            showMessage('step1Message', result.message, 'success');
            
            document.getElementById('investorName').textContent = name;
            
            const step2Button = document.querySelector('#kycVerifyForm button[type="submit"]');
            step2Button.disabled = false;
            
            document.getElementById('step1').style.opacity = '0.6';
            document.querySelector('#step1 button').disabled = true;
            
        } catch (error) {
            showMessage('step1Message', error.message, 'error');
        } finally {
            hideLoading(button);
        }
    });
}

if (document.getElementById('kycVerifyForm')) {
    document.getElementById('kycVerifyForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const button = e.target.querySelector('button[type="submit"]');
        const file = document.getElementById('kycVerifyFile').files[0];
        
        if (!file) {
            alert('Please select an audio file');
            return;
        }
        
        const formData = new FormData();
        formData.append('name', kycName);
        formData.append('file', file);
        
        showLoading(button);
        
        try {
            const result = await apiRequest('/verify', {
                method: 'POST',
                body: formData
            });
            
            verificationResult = result;
            
            const verified = result.verified;
            const percentage = (result.similarity * 100).toFixed(1);
            
            if (verified) {
                showMessage('step2Message', `✓ Identity verified (${percentage}% match)`, 'success');
            } else {
                showMessage('step2Message', `✗ Identity verification failed (${percentage}% match)`, 'error');
            }
            
            const step3Button = document.querySelector('#kycDeepfakeForm button[type="submit"]');
            step3Button.disabled = false;
            
            document.getElementById('step2').style.opacity = '0.6';
            button.disabled = true;
            
        } catch (error) {
            showMessage('step2Message', error.message, 'error');
        } finally {
            hideLoading(button);
        }
    });
}

if (document.getElementById('kycDeepfakeForm')) {
    document.getElementById('kycDeepfakeForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const button = e.target.querySelector('button[type="submit"]');
        const file = document.getElementById('kycDeepfakeFile').files[0];
        
        if (!file) {
            alert('Please select an audio file');
            return;
        }
        
        const formData = new FormData();
        formData.append('file', file);
        
        showLoading(button);
        
        try {
            const result = await apiRequest('/detect-deepfake', {
                method: 'POST',
                body: formData
            });
            
            deepfakeResult = result;
            
            const label = result.label;
            const confidence = (result.confidence * 100).toFixed(1);
            
            if (label === 'Real') {
                showMessage('step3Message', `✓ Audio is genuine (${confidence}% confidence)`, 'success');
            } else {
                showMessage('step3Message', `✗ Deepfake detected (${confidence}% confidence)`, 'error');
            }
            
            document.getElementById('step3').style.opacity = '0.6';
            button.disabled = true;
            
            showKYCDecision();
            
        } catch (error) {
            showMessage('step3Message', error.message, 'error');
        } finally {
            hideLoading(button);
        }
    });
}

function showKYCDecision() {
    if (!verificationResult || !deepfakeResult) return;
    
    const verified = verificationResult.verified;
    const isReal = deepfakeResult.label === 'Real';
    const accessGranted = verified && isReal;
    
    const decisionPanel = document.getElementById('decisionPanel');
    const decisionContent = document.getElementById('decisionContent');
    
    const statusBadge = document.getElementById('kycStatus');
    
    if (accessGranted) {
        statusBadge.textContent = 'Approved';
        statusBadge.className = 'status-badge status-success';
        
        decisionContent.innerHTML = `
            <div class="decision-content decision-granted">
                <div class="decision-title">✓ ACCESS GRANTED</div>
                <p style="font-size: 1.1rem; margin-top: 1rem;">
                    KYC verification completed successfully. You may proceed with your mutual fund investment.
                </p>
                <div class="decision-details">
                    <div class="decision-detail">
                        <span>Voice Match:</span>
                        <span style="color: #22c55e; font-weight: 600;">
                            ${(verificationResult.similarity * 100).toFixed(1)}% ✓
                        </span>
                    </div>
                    <div class="decision-detail">
                        <span>Audio Authenticity:</span>
                        <span style="color: #22c55e; font-weight: 600;">
                            Real (${(deepfakeResult.confidence * 100).toFixed(1)}%) ✓
                        </span>
                    </div>
                    <div class="decision-detail">
                        <span>Final Decision:</span>
                        <span style="color: #22c55e; font-weight: 600;">APPROVED</span>
                    </div>
                </div>
            </div>
        `;
    } else {
        statusBadge.textContent = 'Rejected';
        statusBadge.className = 'status-badge status-failed';
        
        const reasons = [];
        if (!verified) reasons.push('Voice verification failed');
        if (!isReal) reasons.push('Deepfake/manipulation detected');
        
        decisionContent.innerHTML = `
            <div class="decision-content decision-denied">
                <div class="decision-title">✗ ACCESS DENIED</div>
                <p style="font-size: 1.1rem; margin-top: 1rem;">
                    KYC verification failed. Please contact support for assistance.
                </p>
                <div class="decision-details">
                    <div class="decision-detail">
                        <span>Voice Match:</span>
                        <span style="color: ${verified ? '#22c55e' : '#ef4444'}; font-weight: 600;">
                            ${(verificationResult.similarity * 100).toFixed(1)}% ${verified ? '✓' : '✗'}
                        </span>
                    </div>
                    <div class="decision-detail">
                        <span>Audio Authenticity:</span>
                        <span style="color: ${isReal ? '#22c55e' : '#ef4444'}; font-weight: 600;">
                            ${deepfakeResult.label} (${(deepfakeResult.confidence * 100).toFixed(1)}%) ${isReal ? '✓' : '✗'}
                        </span>
                    </div>
                    <div class="decision-detail">
                        <span>Failure Reason:</span>
                        <span style="color: #ef4444; font-weight: 600;">${reasons.join(', ')}</span>
                    </div>
                    <div class="decision-detail">
                        <span>Final Decision:</span>
                        <span style="color: #ef4444; font-weight: 600;">REJECTED</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    decisionPanel.style.display = 'block';
    decisionPanel.scrollIntoView({ behavior: 'smooth' });
}
