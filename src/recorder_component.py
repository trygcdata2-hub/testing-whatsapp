import streamlit as st
import streamlit.components.v1 as components

def inject_screen_recorder():
    recorder_code = """
    <script>
    (function() {
        try {
            const targetDoc = (window.parent && window.parent.document) ? window.parent.document : document;
            
            // Check if recorder already exists
            if (targetDoc.getElementById('screen-recorder-pill-root')) {
                return;
            }

            // Create styles
            const style = targetDoc.createElement('style');
            style.id = 'screen-recorder-styles';
            style.textContent = `
                #screen-recorder-pill-root {
                    position: fixed !important;
                    bottom: 24px !important;
                    right: 28px !important;
                    z-index: 99999999 !important;
                    background: rgba(15, 23, 42, 0.94) !important;
                    backdrop-filter: blur(16px) !important;
                    -webkit-backdrop-filter: blur(16px) !important;
                    border: 1px solid rgba(59, 130, 246, 0.35) !important;
                    border-radius: 9999px !important;
                    padding: 9px 18px !important;
                    display: flex !important;
                    align-items: center !important;
                    gap: 12px !important;
                    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 20px rgba(59, 130, 246, 0.2) !important;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
                    color: #F8FAFC !important;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                }
                #screen-recorder-pill-root:hover {
                    border-color: #3B82F6 !important;
                    box-shadow: 0 12px 35px rgba(0, 0, 0, 0.6), 0 0 25px rgba(59, 130, 246, 0.35) !important;
                }
                .rec-btn-ui {
                    background: linear-gradient(135deg, #EF4444, #DC2626) !important;
                    color: white !important;
                    border: none !important;
                    border-radius: 9999px !important;
                    padding: 7px 15px !important;
                    font-size: 13px !important;
                    font-weight: 700 !important;
                    cursor: pointer !important;
                    display: flex !important;
                    align-items: center !important;
                    gap: 7px !important;
                    transition: transform 0.15s ease, box-shadow 0.2s ease !important;
                    outline: none !important;
                }
                .rec-btn-ui:hover {
                    transform: scale(1.04) !important;
                    box-shadow: 0 0 15px rgba(239, 68, 68, 0.5) !important;
                }
                .stop-btn-ui {
                    background: linear-gradient(135deg, #10B981, #059669) !important;
                    color: white !important;
                    border: none !important;
                    border-radius: 9999px !important;
                    padding: 7px 15px !important;
                    font-size: 13px !important;
                    font-weight: 700 !important;
                    cursor: pointer !important;
                    display: none !important;
                    align-items: center !important;
                    gap: 7px !important;
                    transition: transform 0.15s ease, box-shadow 0.2s ease !important;
                    outline: none !important;
                }
                .stop-btn-ui:hover {
                    transform: scale(1.04) !important;
                    box-shadow: 0 0 15px rgba(16, 185, 129, 0.5) !important;
                }
                .rec-timer-ui {
                    display: none !important;
                    align-items: center !important;
                    gap: 6px !important;
                    font-size: 13px !important;
                    font-weight: 700 !important;
                    color: #F8FAFC !important;
                    font-variant-numeric: tabular-nums !important;
                }
                .rec-dot-ui {
                    width: 10px !important;
                    height: 10px !important;
                    background-color: #EF4444 !important;
                    border-radius: 50% !important;
                    animation: recPulseKeyframe 1.2s infinite ease-in-out !important;
                }
                @keyframes recPulseKeyframe {
                    0% { transform: scale(0.95); opacity: 0.6; box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
                    70% { transform: scale(1.15); opacity: 1; box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
                    100% { transform: scale(0.95); opacity: 0.6; box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
                }
                .rec-status-ui {
                    font-size: 12px !important;
                    color: #94A3B8 !important;
                    font-weight: 500 !important;
                }
            `;
            targetDoc.head.appendChild(style);

            // Create pill container
            const pill = targetDoc.createElement('div');
            pill.id = 'screen-recorder-pill-root';
            pill.innerHTML = `
                <div class="rec-timer-ui" id="recTimerContainer">
                    <div class="rec-dot-ui"></div>
                    <span id="recTimerText">00:00</span>
                    <span style="font-size: 10px; background: rgba(239, 68, 68, 0.2); color: #FCA5A5; padding: 2px 6px; border-radius: 4px; margin-left: 2px;">REC</span>
                </div>
                <div id="recStatusText" class="rec-status-ui">🎥 Walkthrough Recorder</div>
                <button id="startRecBtn" class="rec-btn-ui">
                    <span>🔴</span> Record Demo
                </button>
                <button id="stopRecBtn" class="stop-btn-ui">
                    <span>⏹️</span> Finish & Save
                </button>
            `;
            targetDoc.body.appendChild(pill);

            let mediaRecorder = null;
            let recordedChunks = [];
            let timerInterval = null;
            let startTime = 0;
            let currentStream = null;

            const startBtn = targetDoc.getElementById('startRecBtn');
            const stopBtn = targetDoc.getElementById('stopRecBtn');
            const timerContainer = targetDoc.getElementById('recTimerContainer');
            const timerText = targetDoc.getElementById('recTimerText');
            const statusText = targetDoc.getElementById('recStatusText');

            function updateTimer() {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                const mins = String(Math.floor(elapsed / 60)).padStart(2, '0');
                const secs = String(elapsed % 60).padStart(2, '0');
                timerText.textContent = mins + ':' + secs;
            }

            async function startRecording() {
                try {
                    recordedChunks = [];
                    const nav = (window.parent && window.parent.navigator) ? window.parent.navigator : navigator;
                    if (!nav.mediaDevices || !nav.mediaDevices.getDisplayMedia) {
                        alert("Screen recording is not supported in this browser. Please open in Google Chrome or Microsoft Edge.");
                        return;
                    }

                    const stream = await nav.mediaDevices.getDisplayMedia({
                        video: {
                            cursor: "always",
                            displaySurface: "browser"
                        },
                        audio: false
                    });

                    currentStream = stream;

                    let mimeType = 'video/webm;codecs=vp9';
                    if (!MediaRecorder.isTypeSupported(mimeType)) {
                        mimeType = 'video/webm';
                        if (!MediaRecorder.isTypeSupported(mimeType)) {
                            mimeType = 'video/mp4';
                        }
                    }

                    mediaRecorder = new MediaRecorder(stream, { mimeType: mimeType });

                    mediaRecorder.ondataavailable = function(e) {
                        if (e.data && e.data.size > 0) {
                            recordedChunks.push(e.data);
                        }
                    };

                    mediaRecorder.onstop = function() {
                        clearInterval(timerInterval);
                        finishAndDownload(mimeType);
                    };

                    stream.getVideoTracks()[0].onended = function() {
                        if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                            mediaRecorder.stop();
                        }
                    };

                    mediaRecorder.start(1000);
                    startTime = Date.now();
                    timerInterval = setInterval(updateTimer, 500);

                    startBtn.style.setProperty('display', 'none', 'important');
                    stopBtn.style.setProperty('display', 'flex', 'important');
                    timerContainer.style.setProperty('display', 'flex', 'important');
                    statusText.style.setProperty('display', 'none', 'important');
                    pill.style.borderColor = '#EF4444';

                } catch (err) {
                    console.error("Recording error:", err);
                    if (err.name !== 'NotAllowedError') {
                        alert("Could not start recording: " + err.message);
                    }
                }
            }

            function stopRecording() {
                if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                    mediaRecorder.stop();
                }
                if (currentStream) {
                    currentStream.getTracks().forEach(track => track.stop());
                }
            }

            function finishAndDownload(mimeType) {
                startBtn.style.setProperty('display', 'flex', 'important');
                stopBtn.style.setProperty('display', 'none', 'important');
                timerContainer.style.setProperty('display', 'none', 'important');
                statusText.style.setProperty('display', 'block', 'important');
                statusText.textContent = '⏳ Saving to Downloads...';
                pill.style.borderColor = '#10B981';

                setTimeout(() => {
                    if (recordedChunks.length === 0) {
                        statusText.textContent = '🎥 Walkthrough Recorder';
                        pill.style.borderColor = 'rgba(59, 130, 246, 0.35)';
                        return;
                    }

                    const blob = new Blob(recordedChunks, { type: mimeType });
                    const url = URL.createObjectURL(blob);
                    const a = targetDoc.createElement('a');
                    a.style.display = 'none';
                    a.href = url;
                    
                    const now = new Date();
                    const dateStr = now.toISOString().slice(0, 10).replace(/-/g, '');
                    const timeStr = String(now.getHours()).padStart(2, '0') + String(now.getMinutes()).padStart(2, '0');
                    const ext = mimeType.includes('mp4') ? 'mp4' : 'webm';
                    a.download = `Operations_Dashboard_Demo_${dateStr}_${timeStr}.${ext}`;
                    
                    targetDoc.body.appendChild(a);
                    a.click();
                    
                    statusText.textContent = '✅ Saved to Downloads!';
                    setTimeout(() => {
                        try { targetDoc.body.removeChild(a); } catch(e){}
                        URL.revokeObjectURL(url);
                        statusText.textContent = '🎥 Walkthrough Recorder';
                        pill.style.borderColor = 'rgba(59, 130, 246, 0.35)';
                    }, 5000);
                }, 300);
            }

            startBtn.addEventListener('click', startRecording);
            stopBtn.addEventListener('click', stopRecording);

        } catch (e) {
            console.error("Screen recorder initialization error:", e);
        }
    })();
    </script>
    """
    components.html(recorder_code, height=0, width=0)
