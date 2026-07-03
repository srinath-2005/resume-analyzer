// Global Chart Instances to prevent overlays when redrawing
let atsChartInstance = null;
let skillGapChartInstance = null;
let drawerChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initStudentAnalyze();
});

// ----------------------------------------------------
// THEME SWITCHER LOGIC
// ----------------------------------------------------
function initTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;

    // Load saved preference
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme === 'light') {
        document.body.classList.remove('dark-mode');
        document.body.classList.add('light-mode');
    } else {
        document.body.classList.remove('light-mode');
        document.body.classList.add('dark-mode');
    }

    themeToggle.addEventListener('click', () => {
        if (document.body.classList.contains('dark-mode')) {
            document.body.classList.remove('dark-mode');
            document.body.classList.add('light-mode');
            localStorage.setItem('theme', 'light');
        } else {
            document.body.classList.remove('light-mode');
            document.body.classList.add('dark-mode');
            localStorage.setItem('theme', 'dark');
        }
    });
}

// ----------------------------------------------------
// STUDENT ATS ANALYZER PIPELINE
// ----------------------------------------------------
function initStudentAnalyze() {
    const analyzeForm = document.getElementById('analyze-form');
    if (!analyzeForm) return;

    analyzeForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        const formData = new FormData(analyzeForm);
        const submitBtn = document.getElementById('submit-btn');
        const loaderPanel = document.getElementById('loader-panel');
        const resultsPanel = document.getElementById('results-panel');

        // Toggle visibility to show loading state
        submitBtn.disabled = true;
        loaderPanel.style.display = 'block';
        resultsPanel.style.display = 'none';

        // Scroll to loader
        loaderPanel.scrollIntoView({ behavior: 'smooth' });

        try {
            const response = await fetch('/student/analyze', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.error) {
                alert(data.error);
                loaderPanel.style.display = 'none';
                submitBtn.disabled = false;
                return;
            }

            // Successfully processed. Hide loader and display results dashboard
            loaderPanel.style.display = 'none';
            resultsPanel.style.display = 'block';
            submitBtn.disabled = false;

            renderStudentResults(data.report, data.contact);

        } catch (error) {
            console.error('Analysis error:', error);
            alert('An unexpected server error occurred during resume analysis.');
            loaderPanel.style.display = 'none';
            submitBtn.disabled = false;
        }
    });
}

function renderStudentResults(report, contact) {
    // 1. Render ATS score text and progress bars
    document.getElementById('ats-score-num').textContent = Math.round(report.ats_score);
    
    // Set score descriptor phrase
    const scorePhrase = document.getElementById('score-phrase');
    if (report.ats_score >= 75) {
        scorePhrase.textContent = "Strong Profile Match";
        scorePhrase.style.color = "var(--success-color)";
    } else if (report.ats_score >= 50) {
        scorePhrase.textContent = "Moderate Profile Match";
        scorePhrase.style.color = "var(--warning-color)";
    } else {
        scorePhrase.textContent = "Weak Profile Match";
        scorePhrase.style.color = "var(--danger-color)";
    }

    // Update progress bars
    updateProgressBar('text-sim', report.text_similarity);
    updateProgressBar('skill-sim', report.skill_overlap_score);
    updateProgressBar('section-score', report.section_score);

    // 2. Render Donut Score Chart
    drawAtsDonutChart('atsScoreChart', report.ats_score);

    // 3. Render Skill Chips (Matched vs Missing)
    const matchedWrapper = document.getElementById('matched-skills-chips');
    const missingWrapper = document.getElementById('missing-skills-chips');
    
    document.getElementById('matched-skills-count').textContent = report.matched_skills.length;
    document.getElementById('missing-skills-count').textContent = report.missing_skills.length;

    matchedWrapper.innerHTML = '';
    missingWrapper.innerHTML = '';

    if (report.matched_skills.length > 0) {
        report.matched_skills.forEach(skill => {
            matchedWrapper.innerHTML += `<span class="skill-chip active-chip"><i class="fa-solid fa-check"></i> ${skill}</span>`;
        });
    } else {
        matchedWrapper.innerHTML = '<span class="no-skills-msg">No matching skills detected.</span>';
    }

    if (report.missing_skills.length > 0) {
        report.missing_skills.forEach(skill => {
            missingWrapper.innerHTML += `<span class="skill-chip missing-chip"><i class="fa-solid fa-xmark"></i> ${skill}</span>`;
        });
    } else {
        missingWrapper.innerHTML = '<span class="no-skills-msg">No missing skills! You match all requirements.</span>';
    }

    // 4. Render Skill Gap Bar Chart (visualizing overlap vs gap)
    drawSkillGapBarChart(report.matched_skills.length, report.missing_skills.length);

    // 5. Populate Recommendations list
    const recommendationsList = document.getElementById('recommendations-list');
    recommendationsList.innerHTML = '';

    if (report.recommendations && report.recommendations.length > 0) {
        report.recommendations.forEach(rec => {
            let icon = 'fa-circle-exclamation';
            if (rec.severity === 'high') icon = 'fa-triangle-exclamation';
            if (rec.severity === 'low') icon = 'fa-circle-question';

            recommendationsList.innerHTML += `
                <div class="checklist-item ${rec.severity}">
                    <div class="checklist-icon"><i class="fa-solid ${icon}"></i></div>
                    <div class="checklist-content">
                        <h4>${rec.category}</h4>
                        <p>${rec.message}</p>
                    </div>
                </div>
            `;
        });
    } else {
        recommendationsList.innerHTML = '<div class="alert alert-success"><i class="fa-solid fa-circle-check"></i> Great job! No critical layout or structural improvements needed.</div>';
    }

    // 6. Populate Sentence Rewriter
    const rewritesTbody = document.getElementById('rewrites-tbody');
    rewritesTbody.innerHTML = '';

    if (report.sentence_rewrites && report.sentence_rewrites.length > 0) {
        report.sentence_rewrites.forEach(item => {
            const guidanceChips = item.suggestions.map(s => `<span class="rewrite-guideline">${s}</span>`).join(' ');
            rewritesTbody.innerHTML += `
                <tr>
                    <td><div class="original-sentence">${item.original}</div></td>
                    <td><div class="improved-sentence"><i class="fa-solid fa-wand-magic-sparkles text-success"></i> ${item.rewritten}</div></td>
                    <td>${guidanceChips}</td>
                </tr>
            `;
        });
    } else {
        rewritesTbody.innerHTML = `
            <tr>
                <td colspan="3" class="text-center py-4 text-secondary">
                    <i class="fa-solid fa-circle-check text-success"></i> No weak action verbs detected in your Experience section! Excellent phrasing.
                </td>
            </tr>
        `;
    }

    // Smooth scroll to results
    resultsPanel.scrollIntoView({ behavior: 'smooth' });
}

// Helper to update progress bar widths and values
function updateProgressBar(idPrefix, value) {
    document.getElementById(`${idPrefix}-val`).textContent = `${Math.round(value)}%`;
    const bar = document.getElementById(`${idPrefix}-progress`);
    // Timeout to trigger CSS transition slide effect
    setTimeout(() => {
        bar.style.width = `${value}%`;
    }, 100);
}

// ----------------------------------------------------
// CHART DRAWING UTILITIES (CHART.JS)
// ----------------------------------------------------
function drawAtsDonutChart(canvasId, score, isMini = false) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    
    // Destroy previous instance to avoid overlay glitches
    if (!isMini && atsChartInstance) atsChartInstance.destroy();
    if (isMini && drawerChartInstance) drawerChartInstance.destroy();

    const primaryColor = getComputedStyle(document.body).getPropertyValue('--accent-color').strip() || '#6366f1';
    const trackColor = getComputedStyle(document.body).getPropertyValue('--bg-tertiary').strip() || '#1f2937';
    
    // Choose appropriate color based on score level
    let matchedColor = primaryColor;
    if (score >= 75) matchedColor = '#10b981'; // Success Green
    else if (score < 50) matchedColor = '#ef4444'; // Danger Red

    const data = {
        datasets: [{
            data: [score, 100 - score],
            backgroundColor: [matchedColor, trackColor],
            borderWidth: 0,
            hoverOffset: 0
        }]
    };

    const config = {
        type: 'doughnut',
        data: data,
        options: {
            cutout: '80%',
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                tooltip: { enabled: false },
                legend: { display: false }
            }
        }
    };

    const newChart = new Chart(ctx, config);
    
    if (isMini) {
        drawerChartInstance = newChart;
    } else {
        atsChartInstance = newChart;
    }
}

function drawSkillGapBarChart(matchedCount, missingCount) {
    const ctx = document.getElementById('skillGapChart').getContext('2d');
    
    if (skillGapChartInstance) skillGapChartInstance.destroy();

    const successColor = getComputedStyle(document.body).getPropertyValue('--success-color').strip() || '#10b981';
    const dangerColor = getComputedStyle(document.body).getPropertyValue('--danger-color').strip() || '#ef4444';

    const data = {
        labels: ['Skills Matched', 'Skills Missing (Gap)'],
        datasets: [{
            label: 'Skills Metric',
            data: [matchedCount, missingCount],
            backgroundColor: [successColor, dangerColor],
            borderRadius: 6,
            barThickness: 35
        }]
    };

    const config = {
        type: 'bar',
        data: data,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: true }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        stepSize: 1,
                        color: 'var(--text-secondary)'
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#ffffff' }
                }
            }
        }
    };

    skillGapChartInstance = new Chart(ctx, config);
}

// String strip helper for CSS variable colors
String.prototype.strip = function() {
    return this.replace(/^\s+|\s+$/g, '');
};

// ----------------------------------------------------
// RECRUITER PORTAL CANDIDATE MODAL DRAWER
// ----------------------------------------------------
async function openCandidateDrawer(matchId) {
    const drawer = document.getElementById('candidate-drawer');
    drawer.style.display = 'flex';

    try {
        const response = await fetch(`/api/match/${matchId}`);
        const data = await response.json();

        // Populate drawer contents
        document.getElementById('drawer-cand-name').textContent = data.candidate_name;
        document.getElementById('drawer-cand-contact').innerHTML = `
            <i class="fa-regular fa-envelope"></i> ${data.email || 'N/A'} &nbsp;|&nbsp; 
            <i class="fa-solid fa-phone"></i> ${data.phone || 'N/A'} &nbsp;|&nbsp; 
            <i class="fa-regular fa-file"></i> ${data.filename}
        `;

        document.getElementById('drawer-ats-score').textContent = Math.round(data.ats_score);
        document.getElementById('drawer-text-sim').textContent = `${Math.round(data.text_similarity)}%`;
        document.getElementById('drawer-skill-sim').textContent = `${Math.round(data.skill_overlap_score)}%`;

        document.getElementById('drawer-text-progress').style.width = `${data.text_similarity}%`;
        document.getElementById('drawer-skill-progress').style.width = `${data.skill_overlap_score}%`;

        // Draw donut chart
        drawAtsDonutChart('drawerAtsChart', data.ats_score, true);

        // Matched & Missing Skills
        const matchedChips = document.getElementById('drawer-matched-skills');
        const missingChips = document.getElementById('drawer-missing-skills');
        matchedChips.innerHTML = '';
        missingChips.innerHTML = '';

        if (data.matched_skills.length > 0) {
            data.matched_skills.forEach(s => {
                matchedChips.innerHTML += `<span class="skill-chip active-chip"><i class="fa-solid fa-check"></i> ${s}</span>`;
            });
        } else {
            matchedChips.innerHTML = '<span class="no-skills-msg">No skills matched.</span>';
        }

        if (data.missing_skills.length > 0) {
            data.missing_skills.forEach(s => {
                missingChips.innerHTML += `<span class="skill-chip missing-chip"><i class="fa-solid fa-xmark"></i> ${s}</span>`;
            });
        } else {
            missingChips.innerHTML = '<span class="no-skills-msg">No skill gaps.</span>';
        }

        // Checklist/Suggestions
        const recommendationsList = document.getElementById('drawer-recommendations');
        recommendationsList.innerHTML = '';
        if (data.suggestions && data.suggestions.length > 0) {
            data.suggestions.forEach(rec => {
                let icon = 'fa-circle-exclamation';
                if (rec.severity === 'high') icon = 'fa-triangle-exclamation';
                if (rec.severity === 'low') icon = 'fa-circle-question';

                recommendationsList.innerHTML += `
                    <div class="checklist-item ${rec.severity}" style="padding: 10px 14px;">
                        <div class="checklist-icon" style="font-size: 1rem;"><i class="fa-solid ${icon}"></i></div>
                        <div class="checklist-content">
                            <h4 style="font-size: 0.85rem;">${rec.category}</h4>
                            <p style="font-size: 0.75rem;">${rec.message}</p>
                        </div>
                    </div>
                `;
            });
        } else {
            recommendationsList.innerHTML = '<div class="alert alert-success" style="padding: 10px 14px; font-size: 0.8rem;"><i class="fa-solid fa-circle-check"></i> Profile is fully complete.</div>';
        }

        // Sentence Rewrites
        const rewritesTbody = document.getElementById('drawer-rewrites');
        rewritesTbody.innerHTML = '';
        if (data.rewrites && data.rewrites.length > 0) {
            data.rewrites.forEach(item => {
                rewritesTbody.innerHTML += `
                    <tr>
                        <td><div class="original-sentence" style="font-size: 0.8rem;">${item.original}</div></td>
                        <td><div class="improved-sentence" style="font-size: 0.8rem;"><i class="fa-solid fa-wand-magic-sparkles text-success"></i> ${item.rewritten}</div></td>
                    </tr>
                `;
            });
        } else {
            rewritesTbody.innerHTML = '<tr><td colspan="2" class="text-center text-secondary py-3" style="font-size: 0.8rem;">No weak verbs detected.</td></tr>';
        }

    } catch (error) {
        console.error('Error fetching candidate match details:', error);
        alert('Could not fetch candidate matching report.');
        closeCandidateDrawer();
    }
}

function closeCandidateDrawer() {
    document.getElementById('candidate-drawer').style.display = 'none';
    if (drawerChartInstance) {
        drawerChartInstance.destroy();
        drawerChartInstance = null;
    }
}
