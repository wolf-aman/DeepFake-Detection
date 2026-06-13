const state = {
    kycName: '',
    verificationResult: null,
    deepfakeResult: null,
};

const $ = (id) => document.getElementById(id);

function clearElement(element) {
    if (!element) return;
    while (element.firstChild) element.removeChild(element.firstChild);
}

function appendText(parent, tag, text, className = '') {
    const node = document.createElement(tag);
    node.textContent = text;
    if (className) node.className = className;
    parent.appendChild(node);
    return node;
}

function percentage(value) {
    return `${(Number(value || 0) * 100).toFixed(1)}%`;
}

function clampPercent(value) {
    const numeric = Math.max(0, Math.min(100, Number(value || 0) * 100));
    return `${numeric.toFixed(1)}%`;
}

async function apiRequest(url, options = {}) {
    const response = await fetch(url, options);
    let data = null;

    try {
        data = await response.json();
    } catch (_) {
        data = {};
    }

    if (!response.ok) {
        throw new Error(data.detail || `Request failed with status ${response.status}`);
    }

    return data;
}

function showLoading(button) {
    if (!button) return;
    button.disabled = true;
    const text = button.querySelector('.btn-text');
    const loader = button.querySelector('.loader');
    if (text) text.hidden = true;
    if (loader) loader.hidden = false;
}

function hideLoading(button) {
    if (!button) return;
    button.disabled = false;
    const text = button.querySelector('.btn-text');
    const loader = button.querySelector('.loader');
    if (text) text.hidden = false;
    if (loader) loader.hidden = true;
}

function showMessage(elementId, message, type) {
    const element = $(elementId);
    if (!element) return;
    element.textContent = message;
    element.className = `message ${type}`;
    element.hidden = false;

    window.setTimeout(() => {
        element.hidden = true;
    }, 5000);
}

function setResultVisible(element, visible = true) {
    if (!element) return;
    element.className = visible ? 'result show' : 'result';
}

async function loadSpeakers() {
    const container = $('speakersTable');
    if (!container) return;

    try {
        const speakers = await apiRequest('/speakers');
        clearElement(container);
        updateSpeakerDropdown(speakers);

        if (!speakers.length) {
            appendText(container, 'p', 'No speakers enrolled yet.', 'loading');
            return;
        }

        const table = document.createElement('table');
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        ['Name', 'Enrolled At', 'Action'].forEach((heading) => appendText(headerRow, 'th', heading));
        thead.appendChild(headerRow);
        table.appendChild(thead);

        const tbody = document.createElement('tbody');
        speakers.forEach((speaker) => {
            const row = document.createElement('tr');
            appendText(row, 'td', speaker.name || 'Unknown');
            appendText(row, 'td', formatDate(speaker.created_at));

            const actionCell = document.createElement('td');
            const deleteButton = document.createElement('button');
            deleteButton.type = 'button';
            deleteButton.className = 'btn btn-danger';
            deleteButton.textContent = 'Delete';
            deleteButton.addEventListener('click', () => deleteSpeaker(speaker.slug || speaker.name));
            actionCell.appendChild(deleteButton);
            row.appendChild(actionCell);
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        container.appendChild(table);
    } catch (error) {
        clearElement(container);
        appendText(container, 'p', `Failed to load speakers: ${error.message}`, 'message error');
    }
}

function formatDate(value) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return 'Unknown';
    return date.toLocaleString();
}

function updateSpeakerDropdown(speakers) {
    const dropdown = $('verifySpeaker');
    if (!dropdown) return;

    clearElement(dropdown);
    const placeholder = document.createElement('option');
    placeholder.value = '';
    placeholder.textContent = '-- Select a speaker --';
    dropdown.appendChild(placeholder);

    speakers.forEach((speaker) => {
        const option = document.createElement('option');
        option.value = speaker.slug || speaker.name;
        option.textContent = speaker.name;
        dropdown.appendChild(option);
    });
}

async function deleteSpeaker(identifier) {
    if (!window.confirm('Are you sure you want to delete this speaker?')) return;

    try {
        await apiRequest(`/speakers/${encodeURIComponent(identifier)}`, { method: 'DELETE' });
        showMessage('enrollMessage', 'Speaker deleted successfully.', 'success');
        await loadSpeakers();
    } catch (error) {
        showMessage('enrollMessage', `Failed to delete speaker: ${error.message}`, 'error');
    }
}

function buildAudioFormData(name, fileInputId, filesInputId) {
    const formData = new FormData();
    if (name !== null) formData.append('name', name);

    if (filesInputId) {
        const files = $(filesInputId).files;
        for (const file of files) formData.append('files', file);
    }

    if (fileInputId) {
        const file = $(fileInputId).files[0];
        if (file) formData.append('file', file);
    }

    return formData;
}

function renderVerificationResult(container, result) {
    clearElement(container);

    const verified = Boolean(result.verified);
    const score = percentage(result.similarity);

    appendText(container, 'div', score, 'similarity-score');

    const progressBar = document.createElement('div');
    progressBar.className = 'progress-bar';
    const progressFill = document.createElement('div');
    progressFill.className = `progress-fill ${verified ? 'verified' : 'not-verified'}`;
    progressFill.style.width = clampPercent(result.similarity);
    progressBar.appendChild(progressFill);
    container.appendChild(progressBar);

    appendText(container, 'div', verified ? '✓ VERIFIED' : '✗ NOT VERIFIED', `verification-status ${verified ? 'verified' : 'not-verified'}`);
    appendText(container, 'p', `Threshold: ${(result.threshold * 100).toFixed(0)}% | Similarity: ${score}`, 'muted');
    setResultVisible(container, true);
}

function renderDeepfakeResult(container, result) {
    clearElement(container);

    const label = result.label || 'Unknown';
    appendText(container, 'div', label.toUpperCase(), `deepfake-badge ${label.toLowerCase()}`);
    appendText(container, 'div', `Confidence: ${percentage(result.confidence)}`, 'confidence');
    appendText(container, 'div', result.explanation || 'No explanation returned.', 'explanation');

    if (result.raw_label) {
        appendText(container, 'p', `Raw model label: ${result.raw_label}`, 'muted');
    }
    setResultVisible(container, true);
}

function renderErrorResult(container, message) {
    clearElement(container);
    appendText(container, 'p', message, 'message error');
    setResultVisible(container, true);
}

function bindMainDemoForms() {
    const enrollForm = $('enrollForm');
    if (enrollForm) {
        enrollForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const button = event.target.querySelector('button[type="submit"]');
            const name = $('enrollName').value;
            const files = $('enrollFiles').files;

            if (!files.length) {
                showMessage('enrollMessage', 'Please select at least one audio file.', 'error');
                return;
            }

            showLoading(button);
            try {
                const result = await apiRequest('/enroll', {
                    method: 'POST',
                    body: buildAudioFormData(name, null, 'enrollFiles'),
                });
                showMessage('enrollMessage', result.message, 'success');
                enrollForm.reset();
                await loadSpeakers();
            } catch (error) {
                showMessage('enrollMessage', error.message, 'error');
            } finally {
                hideLoading(button);
            }
        });
    }

    const verifyForm = $('verifyForm');
    if (verifyForm) {
        verifyForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const button = event.target.querySelector('button[type="submit"]');
            const name = $('verifySpeaker').value;
            const file = $('verifyFile').files[0];
            const resultDiv = $('verifyResult');

            if (!name || !file) {
                renderErrorResult(resultDiv, 'Please select both a speaker and an audio file.');
                return;
            }

            showLoading(button);
            setResultVisible(resultDiv, false);
            try {
                const result = await apiRequest('/verify', {
                    method: 'POST',
                    body: buildAudioFormData(name, 'verifyFile', null),
                });
                renderVerificationResult(resultDiv, result);
            } catch (error) {
                renderErrorResult(resultDiv, error.message);
            } finally {
                hideLoading(button);
            }
        });
    }

    const deepfakeForm = $('deepfakeForm');
    if (deepfakeForm) {
        deepfakeForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const button = event.target.querySelector('button[type="submit"]');
            const file = $('deepfakeFile').files[0];
            const resultDiv = $('deepfakeResult');

            if (!file) {
                renderErrorResult(resultDiv, 'Please select an audio file.');
                return;
            }

            showLoading(button);
            setResultVisible(resultDiv, false);
            try {
                const result = await apiRequest('/detect-deepfake', {
                    method: 'POST',
                    body: buildAudioFormData(null, 'deepfakeFile', null),
                });
                renderDeepfakeResult(resultDiv, result);
            } catch (error) {
                renderErrorResult(resultDiv, error.message);
            } finally {
                hideLoading(button);
            }
        });
    }
}

function bindKycForms() {
    const kycEnrollForm = $('kycEnrollForm');
    if (kycEnrollForm) {
        kycEnrollForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const button = event.target.querySelector('button[type="submit"]');
            const name = $('kycName').value;
            const files = $('kycEnrollFiles').files;

            if (files.length < 3) {
                showMessage('step1Message', 'Please upload at least 3 audio files.', 'error');
                return;
            }

            showLoading(button);
            try {
                const result = await apiRequest('/enroll', {
                    method: 'POST',
                    body: buildAudioFormData(name, null, 'kycEnrollFiles'),
                });
                state.kycName = result.slug || name;
                $('investorName').textContent = result.name || name;
                showMessage('step1Message', result.message, 'success');
                completeStep('step1');
                enableFormButton('kycVerifyForm');
            } catch (error) {
                showMessage('step1Message', error.message, 'error');
            } finally {
                hideLoading(button);
            }
        });
    }

    const kycVerifyForm = $('kycVerifyForm');
    if (kycVerifyForm) {
        kycVerifyForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const button = event.target.querySelector('button[type="submit"]');
            const file = $('kycVerifyFile').files[0];

            if (!state.kycName) {
                showMessage('step2Message', 'Please complete enrollment first.', 'error');
                return;
            }
            if (!file) {
                showMessage('step2Message', 'Please select an audio file.', 'error');
                return;
            }

            showLoading(button);
            try {
                const result = await apiRequest('/verify', {
                    method: 'POST',
                    body: buildAudioFormData(state.kycName, 'kycVerifyFile', null),
                });
                state.verificationResult = result;
                const type = result.verified ? 'success' : 'error';
                const symbol = result.verified ? '✓' : '✗';
                showMessage('step2Message', `${symbol} Identity ${result.verified ? 'verified' : 'verification failed'} (${percentage(result.similarity)} match)`, type);
                completeStep('step2');
                enableFormButton('kycDeepfakeForm');
            } catch (error) {
                showMessage('step2Message', error.message, 'error');
            } finally {
                hideLoading(button);
            }
        });
    }

    const kycDeepfakeForm = $('kycDeepfakeForm');
    if (kycDeepfakeForm) {
        kycDeepfakeForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const button = event.target.querySelector('button[type="submit"]');
            const file = $('kycDeepfakeFile').files[0];

            if (!file) {
                showMessage('step3Message', 'Please select an audio file.', 'error');
                return;
            }

            showLoading(button);
            try {
                const result = await apiRequest('/detect-deepfake', {
                    method: 'POST',
                    body: buildAudioFormData(null, 'kycDeepfakeFile', null),
                });
                state.deepfakeResult = result;
                const isReal = result.label === 'Real';
                const type = isReal ? 'success' : 'error';
                const symbol = isReal ? '✓' : '✗';
                showMessage('step3Message', `${symbol} Audio authenticity: ${result.label} (${percentage(result.confidence)} confidence)`, type);
                completeStep('step3');
                showKYCDecision();
            } catch (error) {
                showMessage('step3Message', error.message, 'error');
            } finally {
                hideLoading(button);
            }
        });
    }
}

function completeStep(stepId) {
    const step = $(stepId);
    if (step) step.classList.add('completed');
    const button = step?.querySelector('button[type="submit"]');
    if (button) button.disabled = true;
}

function enableFormButton(formId) {
    const button = document.querySelector(`#${formId} button[type="submit"]`);
    if (button) button.disabled = false;
}

function showKYCDecision() {
    if (!state.verificationResult || !state.deepfakeResult) return;

    const verified = Boolean(state.verificationResult.verified);
    const isReal = state.deepfakeResult.label === 'Real';
    const accessGranted = verified && isReal;

    const statusBadge = $('kycStatus');
    statusBadge.textContent = accessGranted ? 'Approved' : 'Rejected';
    statusBadge.className = `status-badge ${accessGranted ? 'status-success' : 'status-failed'}`;

    const panel = $('decisionPanel');
    const content = $('decisionContent');
    clearElement(content);

    const wrapper = document.createElement('div');
    wrapper.className = `decision-content ${accessGranted ? 'decision-granted' : 'decision-denied'}`;
    appendText(wrapper, 'div', accessGranted ? '✓ ACCESS GRANTED' : '✗ ACCESS DENIED', 'decision-title');
    appendText(
        wrapper,
        'p',
        accessGranted
            ? 'KYC verification completed successfully. You may proceed with your mutual fund investment.'
            : 'KYC verification failed. Please contact support for assistance.'
    );

    const details = document.createElement('div');
    details.className = 'decision-details';
    addDecisionRow(details, 'Voice Match:', `${percentage(state.verificationResult.similarity)} ${verified ? '✓' : '✗'}`, verified);
    addDecisionRow(details, 'Audio Authenticity:', `${state.deepfakeResult.label} (${percentage(state.deepfakeResult.confidence)}) ${isReal ? '✓' : '✗'}`, isReal);
    addDecisionRow(details, 'Final Decision:', accessGranted ? 'APPROVED' : 'REJECTED', accessGranted);

    if (!accessGranted) {
        const reasons = [];
        if (!verified) reasons.push('Voice verification failed');
        if (!isReal) reasons.push('Deepfake/manipulation detected');
        addDecisionRow(details, 'Failure Reason:', reasons.join(', '), false);
    }

    wrapper.appendChild(details);
    content.appendChild(wrapper);
    panel.hidden = false;
    panel.scrollIntoView({ behavior: 'smooth' });
}

function addDecisionRow(parent, label, value, success) {
    const row = document.createElement('div');
    row.className = 'decision-detail';
    appendText(row, 'span', label);
    appendText(row, 'span', value, success ? 'text-success' : 'text-danger');
    parent.appendChild(row);
}

function init() {
    bindMainDemoForms();
    bindKycForms();

    const refreshBtn = $('refreshBtn');
    if (refreshBtn) refreshBtn.addEventListener('click', loadSpeakers);
    if ($('speakersTable')) loadSpeakers();
}

document.addEventListener('DOMContentLoaded', init);
