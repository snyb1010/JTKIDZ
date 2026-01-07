let html5QrCode;
let todayCount = 0;

// Show status message
function showMessage(message, type) {
    const statusDiv = document.getElementById('status-message');
    statusDiv.className = `p-4 rounded-lg mb-4 ${
        type === 'success' ? 'bg-green-100 text-green-800' :
        type === 'error' ? 'bg-red-100 text-red-800' :
        type === 'warning' ? 'bg-yellow-100 text-yellow-800' :
        'bg-blue-100 text-blue-800'
    }`;
    statusDiv.textContent = message;
    statusDiv.classList.remove('hidden');
    
    setTimeout(() => {
        statusDiv.classList.add('hidden');
    }, 5000);
}

// Submit barcode to server
async function submitBarcode(barcode) {
    try {
        const response = await fetch('/attendance/record', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ barcode: barcode.trim().toUpperCase() })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showMessage(`✅ ${data.message}`, 'success');
            todayCount++;
            document.getElementById('today-count').textContent = todayCount;
            
            // Play success sound (optional)
            if (window.AudioContext) {
                const audioContext = new AudioContext();
                const oscillator = audioContext.createOscillator();
                oscillator.type = 'sine';
                oscillator.frequency.setValueAtTime(600, audioContext.currentTime);
                oscillator.connect(audioContext.destination);
                oscillator.start();
                oscillator.stop(audioContext.currentTime + 0.1);
            }
        } else {
            showMessage(data.message || 'Error recording attendance', 'error');
        }
    } catch (error) {
        showMessage('Network error. Please check connection.', 'error');
        console.error('Error:', error);
    }
}

// Start scanner
function startScanner() {
    const startBtn = document.getElementById('start-scan');
    const stopBtn = document.getElementById('stop-scan');
    
    html5QrCode = new Html5Qrcode("reader");
    
    const config = {
        fps: 10,
        qrbox: { width: 250, height: 150 }
    };
    
    html5QrCode.start(
        { facingMode: "environment" },
        config,
        (decodedText, decodedResult) => {
            // Barcode scanned successfully
            submitBarcode(decodedText);
        },
        (errorMessage) => {
            // Scanning error (ignore most)
        }
    ).then(() => {
        startBtn.classList.add('hidden');
        stopBtn.classList.remove('hidden');
    }).catch((err) => {
        showMessage('Camera error: ' + err, 'error');
    });
}

// Stop scanner
function stopScanner() {
    const startBtn = document.getElementById('start-scan');
    const stopBtn = document.getElementById('stop-scan');
    
    if (html5QrCode) {
        html5QrCode.stop().then(() => {
            startBtn.classList.remove('hidden');
            stopBtn.classList.add('hidden');
        }).catch((err) => {
            console.error('Stop error:', err);
        });
    }
}

// Event listeners
document.getElementById('start-scan').addEventListener('click', startScanner);
document.getElementById('stop-scan').addEventListener('click', stopScanner);

// Manual form submission
document.getElementById('manual-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const barcode = document.getElementById('manual-barcode').value;
    if (barcode) {
        submitBarcode(barcode);
        document.getElementById('manual-barcode').value = '';
    }
});

// Load today's count on page load
window.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/attendance/today');
        if (response.ok) {
            const text = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(text, 'text/html');
            const rows = doc.querySelectorAll('tbody tr');
            todayCount = rows.length;
            document.getElementById('today-count').textContent = todayCount;
        }
    } catch (error) {
        console.error('Error loading count:', error);
    }
});
