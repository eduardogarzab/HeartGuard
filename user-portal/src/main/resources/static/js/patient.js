(function () {
    const body = document.body;
    const patientId = body.getAttribute('data-patient-id');
    if (!patientId) {
        return;
    }

    const chartCanvas = document.getElementById('signalChart');
    const buttons = document.querySelectorAll('.tab-button');
    let chart;

    function renderChart(signal, labels, values) {
        if (!chartCanvas) {
            return;
        }
        if (chart) {
            chart.destroy();
        }
        chart = new Chart(chartCanvas, {
            type: 'line',
            data: {
                labels,
                datasets: [{
                    label: signal.toUpperCase(),
                    data: values,
                    borderColor: '#ff4d6d',
                    tension: 0.3,
                    pointRadius: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        ticks: {
                            maxRotation: 0,
                            autoSkip: true
                        }
                    }
                }
            }
        });
    }

    async function loadSignal(signal) {
        try {
            const response = await fetch(`/patient/${patientId}/stream?signal=${signal}`);
            if (!response.ok) {
                throw new Error('No se pudo cargar la señal');
            }
            const payload = await response.json();
            const data = payload.data || [];
            const labels = data.map(point => point.timestamp);
            const values = data.map(point => point.value);
            renderChart(signal, labels, values);
        } catch (error) {
            console.error(error);
        }
    }

    function setActive(button) {
        buttons.forEach(btn => btn.classList.remove('active'));
        button.classList.add('active');
    }

    buttons.forEach(button => {
        button.addEventListener('click', () => {
            const signal = button.getAttribute('data-signal');
            setActive(button);
            loadSignal(signal);
        });
    });

    if (buttons.length > 0) {
        setActive(buttons[0]);
        loadSignal(buttons[0].getAttribute('data-signal'));
    }
})();
