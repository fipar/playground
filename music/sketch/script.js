document.addEventListener('DOMContentLoaded', () => {
    const audioFileInput = document.getElementById('audioFile');
    const bpmInput = document.getElementById('bpm');
    const canvas = document.getElementById('soundCanvas');
    const playButton = document.getElementById('playButton');
    const clearButton = document.getElementById('clearButton');
    const saveButton = document.getElementById('saveButton');

    const ctx = canvas.getContext('2d');
    let audioContext;
    let audioBuffer;
    let mediaRecorder;
    let recordedChunks = [];

    const CANVAS_WIDTH = 800;
    const CANVAS_HEIGHT = 400;
    canvas.width = CANVAS_WIDTH;
    canvas.height = CANVAS_HEIGHT;

    const baseMidiNote = 36; // C2
    const numNotes = 24;
    const noteNames = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
    const noteHeight = CANVAS_HEIGHT / numNotes;

    const totalSeconds = 10; // Canvas represents 10 seconds

    let isDrawing = false;
    let drawnPath = []; // Array of {x, y, isStartingPoint}

    function initAudioContext() {
        if (!audioContext) {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log("AudioContext initialized. State:", audioContext.state);
        }
    }

    audioFileInput.addEventListener('change', async (event) => {
        initAudioContext();
        if (audioContext.state === 'suspended') {
            await audioContext.resume(); // Resume context on user gesture
            console.log("AudioContext resumed on file load. State:", audioContext.state);
        }

        const file = event.target.files[0];
        if (file) {
            try {
                const arrayBuffer = await file.arrayBuffer();
                audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
                playButton.disabled = false;
                saveButton.disabled = true;
                console.log("Audio file loaded and decoded. Duration:", audioBuffer.duration);
                console.log("Buffer details:", audioBuffer);
            } catch (error) {
                console.error("Error decoding audio data:", error);
                alert("Error decoding audio file. Check console for details.");
                playButton.disabled = true;
                audioBuffer = null;
            }
        }
    });

    function drawGrid() {
        ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
        ctx.strokeStyle = '#ccc';
        ctx.lineWidth = 0.5;

        for (let i = 0; i <= totalSeconds; i++) {
            const x = (i / totalSeconds) * CANVAS_WIDTH;
            ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, CANVAS_HEIGHT); ctx.stroke();
            if (i < totalSeconds) {
                ctx.fillStyle = '#888'; ctx.font = '10px Arial';
                ctx.fillText(`${i}s`, x + 5, 15);
            }
        }

        for (let i = 0; i <= numNotes; i++) {
            const y = i * noteHeight;
            ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(CANVAS_WIDTH, y); ctx.stroke();
            if (i < numNotes) {
                const currentMidi = baseMidiNote + (numNotes - 1 - i);
                const noteIndex = currentMidi % 12;
                const octave = Math.floor(currentMidi / 12); // Standard MIDI octave
                const noteName = `${noteNames[noteIndex]}${octave}`;
                ctx.fillStyle = '#888'; ctx.font = '10px Arial';
                ctx.fillText(noteName, 5, y - 3 < 0 ? 10 : y - 3); // Adjust text position if near top
            }
        }
    }

    function getMousePos(event) {
        const rect = canvas.getBoundingClientRect();
        return { x: event.clientX - rect.left, y: event.clientY - rect.top };
    }

    canvas.addEventListener('mousedown', (event) => {
        if (!audioBuffer) {
            alert("Please upload an audio sample first."); return;
        }
        isDrawing = true;
        const pos = getMousePos(event);
        drawnPath.push({ x: pos.x, y: pos.y, isStartingPoint: true });
        drawPath();
    });

    canvas.addEventListener('mousemove', (event) => {
        if (!isDrawing) return;
        const pos = getMousePos(event);
        drawnPath.push({ x: pos.x, y: pos.y, isStartingPoint: false });
        drawPath();
    });

    canvas.addEventListener('mouseup', () => { isDrawing = false; });
    canvas.addEventListener('mouseleave', () => { isDrawing = false; });

    function drawPath() {
        drawGrid();
        if (drawnPath.length < 1) return;
        ctx.strokeStyle = '#007bff'; ctx.lineWidth = 3;
        ctx.beginPath();
        let currentSubPathStarted = false;
        for (const point of drawnPath) {
            if (point.isStartingPoint) {
                ctx.moveTo(point.x, point.y);
                currentSubPathStarted = true;
            } else if (currentSubPathStarted) {
                ctx.lineTo(point.x, point.y);
            } else { // Should not happen if first point is always isStartingPoint=true
                ctx.moveTo(point.x, point.y);
                currentSubPathStarted = true;
            }
        }
        ctx.stroke();
    }

    clearButton.addEventListener('click', () => {
        drawnPath = [];
        drawGrid();
        saveButton.disabled = true;
        if (mediaRecorder && mediaRecorder.state === "recording") {
            mediaRecorder.stop();
            console.log("Recording stopped by clear button.");
        }
    });

    function yToPlaybackRate(y) {
        const invertedY = CANVAS_HEIGHT - y;
        let noteIndexFromTop = Math.floor(invertedY / noteHeight);
        noteIndexFromTop = Math.max(0, Math.min(numNotes - 1, noteIndexFromTop)); // Clamp
        const midiNote = baseMidiNote + noteIndexFromTop;
        const refMidiNote = baseMidiNote; // Or could be the original pitch of the sample if known
        const semitonesDifference = midiNote - refMidiNote;
        return Math.pow(2, semitonesDifference / 12);
    }

    function xToTime(x) { // Removed BPM from here, as X axis is absolute time
        return Math.max(0, (x / CANVAS_WIDTH) * totalSeconds);
    }

    playButton.addEventListener('click', async () => {
        if (!audioBuffer || drawnPath.length === 0) {
            alert("Please load a sample and draw something."); return;
        }
        initAudioContext(); // Ensure context exists

        if (audioContext.state === 'suspended') {
            await audioContext.resume();
            console.log("AudioContext resumed on play. State:", audioContext.state);
        }
        if (audioContext.state !== 'running') {
            console.error("AudioContext is not running. Current state:", audioContext.state);
            alert("AudioContext is not running. Please interact with the page (e.g., click) and try again.");
            return;
        }

        const currentTime = audioContext.currentTime;
        console.log("Playback initiated. AudioContext current time:", currentTime);
        let activeSources = [];

        const dest = audioContext.createMediaStreamDestination();
        try {
            mediaRecorder = new MediaRecorder(dest.stream, { mimeType: 'audio/webm;codecs=opus' });
        } catch (e) {
            console.warn("WebM with Opus not supported, trying audio/wav", e);
            try {
                 mediaRecorder = new MediaRecorder(dest.stream, { mimeType: 'audio/wav' });
            } catch (e2) {
                console.error("Failed to create MediaRecorder with supported type", e2);
                alert("MediaRecorder could not be initialized. Saving might not work.");
                // Optionally, allow playback without recording if MediaRecorder fails
            }
        }
        
        if (mediaRecorder) {
            recordedChunks = [];
            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) recordedChunks.push(event.data);
            };
            mediaRecorder.onstop = () => {
                saveButton.disabled = false;
                console.log("Recording stopped. Chunks available:", recordedChunks.length);
            };
            mediaRecorder.start();
            console.log("MediaRecorder started. State:", mediaRecorder.state);
        }


        // Playback logic: Iterate through segments of the drawn path
        for (let i = 0; i < drawnPath.length; i++) {
            const p1 = drawnPath[i];

            if (i + 1 < drawnPath.length) { // If there's a next point to form a segment
                const p2 = drawnPath[i+1];
                if (p2.isStartingPoint) { // p1 is an end of a line or isolated point
                    // Play p1 as a short note
                    const segmentStartTimeOnTimeline = currentTime + xToTime(p1.x);
                    const playbackRate = yToPlaybackRate(p1.y);
                    const timelineSegmentDuration = 0.1; // Default for end/isolated point
                    let bufferContentDuration = timelineSegmentDuration * playbackRate;
                    bufferContentDuration = Math.min(bufferContentDuration, audioBuffer.duration);

                    if (playbackRate > 0 && !isNaN(playbackRate) && bufferContentDuration > 0.001) {
                        const source = audioContext.createBufferSource();
                        source.buffer = audioBuffer;
                        source.playbackRate.value = playbackRate;
                        source.connect(audioContext.destination);
                        if (mediaRecorder) source.connect(dest);
                        console.log(`Scheduling isolated/end point p1: Time=${segmentStartTimeOnTimeline.toFixed(3)}, Rate=${playbackRate.toFixed(2)}, BufDur=${bufferContentDuration.toFixed(3)}`);
                        source.start(segmentStartTimeOnTimeline, 0, bufferContentDuration);
                        activeSources.push(source);
                    }
                    continue; // Move to p2 which starts a new line
                }

                // This is a segment from p1 to p2
                const segmentStartTimeOnTimeline = currentTime + xToTime(p1.x);
                const segmentEndTimeOnTimeline = currentTime + xToTime(p2.x);
                const timelineSegmentDuration = segmentEndTimeOnTimeline - segmentStartTimeOnTimeline;

                if (timelineSegmentDuration <= 0.001) {
                    // console.warn("Segment too short, skipping:", timelineSegmentDuration);
                    continue;
                }

                const playbackRate = yToPlaybackRate(p1.y); // Pitch at the start of segment

                if (playbackRate <= 0 || isNaN(playbackRate)) {
                    console.warn("Invalid playbackRate for segment, skipping. Rate:", playbackRate, "Y:", p1.y);
                    continue;
                }

                let bufferContentDuration = timelineSegmentDuration * playbackRate;
                bufferContentDuration = Math.min(bufferContentDuration, audioBuffer.duration); // Clamp to buffer's actual length

                if (bufferContentDuration <= 0.001) {
                    // console.warn("Buffer content duration too short, skipping segment:", bufferContentDuration);
                    continue;
                }

                const source = audioContext.createBufferSource();
                source.buffer = audioBuffer;
// Inside the scheduling loop
const gainNode = audioContext.createGain();
gainNode.gain.value = 2.0; // Boost volume (be careful with clipping)

source.connect(gainNode);
gainNode.connect(audioContext.destination);
if (mediaRecorder) gainNode.connect(dest); // also connect gain to recorder
                source.playbackRate.value = playbackRate;
                source.connect(audioContext.destination);
                 if (mediaRecorder) source.connect(dest);

                console.log(
                    `Scheduling segment [${i}]: P1(${p1.x.toFixed(1)},${p1.y.toFixed(1)}) P2(${p2.x.toFixed(1)},${p2.y.toFixed(1)})
                    \tTime: ${segmentStartTimeOnTimeline.toFixed(3)}s (TimelineDur: ${timelineSegmentDuration.toFixed(3)}s)
                    \tRate: ${playbackRate.toFixed(2)}, BufDur: ${bufferContentDuration.toFixed(3)}s (Offset: 0)`
                );
                source.start(segmentStartTimeOnTimeline, 0, bufferContentDuration);
                activeSources.push(source);

            } else { // This is the very last point in drawnPath
                const segmentStartTimeOnTimeline = currentTime + xToTime(p1.x);
                const playbackRate = yToPlaybackRate(p1.y);
                const timelineSegmentDuration = 0.1; // Default for the last point
                let bufferContentDuration = timelineSegmentDuration * playbackRate;
                bufferContentDuration = Math.min(bufferContentDuration, audioBuffer.duration);

                if (playbackRate > 0 && !isNaN(playbackRate) && bufferContentDuration > 0.001) {
                    const source = audioContext.createBufferSource();
                    source.buffer = audioBuffer;
                    source.playbackRate.value = playbackRate;
                    source.connect(audioContext.destination);
                    if (mediaRecorder) source.connect(dest);
                    console.log(`Scheduling final point: Time=${segmentStartTimeOnTimeline.toFixed(3)}, Rate=${playbackRate.toFixed(2)}, BufDur=${bufferContentDuration.toFixed(3)}`);
                    source.start(segmentStartTimeOnTimeline, 0, bufferContentDuration);
                    activeSources.push(source);
                }
            }
        }


        // Stop recording logic
        let maxPossibleEndTime = currentTime;
        if (drawnPath.length > 0) {
            const lastPoint = drawnPath[drawnPath.length - 1];
            maxPossibleEndTime = currentTime + xToTime(lastPoint.x) + 0.2; // Add buffer for last note's tail
        } else {
            maxPossibleEndTime = currentTime + 0.1; // If nothing drawn, stop quickly
        }
        
        const recorderStopDelay = Math.max(100, (maxPossibleEndTime - audioContext.currentTime + 0.5) * 1000); // ensure positive delay in ms

        console.log(`Calculated max end time for audio: ${maxPossibleEndTime.toFixed(3)}. Recorder stop delay: ${recorderStopDelay.toFixed(0)}ms`);

        if (mediaRecorder) {
            setTimeout(() => {
                if (mediaRecorder.state === "recording") {
                    mediaRecorder.stop();
                    console.log("MediaRecorder stopped via timeout.");
                }
            }, recorderStopDelay);
        }
    });

    saveButton.addEventListener('click', () => {
        if (!recordedChunks || recordedChunks.length === 0) {
            alert("No audio recorded or recording is empty. Play something first.");
            return;
        }
        const blob = new Blob(recordedChunks, { type: mediaRecorder.mimeType || 'audio/webm' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none'; a.href = url;
        const extension = (mediaRecorder.mimeType && mediaRecorder.mimeType.includes('wav')) ? 'wav' : 'webm';
        a.download = `sketched_sound.${extension}`;
        document.body.appendChild(a); a.click();
        window.URL.revokeObjectURL(url); document.body.removeChild(a);
        saveButton.disabled = true; // Disable after saving, until new recording
        recordedChunks = []; // Clear for next recording
        console.log("Saved audio file.");
    });

    drawGrid(); // Initial draw
});
