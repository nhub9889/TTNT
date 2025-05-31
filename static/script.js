// Khai báo biến toàn cục
let map;
let startMarker = null;
let endMarker = null;
let routeLine = null;
let currentStart = null;
let currentEnd = null;
let currentRouteDetails = null;
let chargingMarkers = [];

function initMap() {
    map = L.map('map').setView([10.7769, 106.7009], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
    }).addTo(map);

    loadChargingStations();

    document.getElementById('close-steps').addEventListener('click', () => {
        document.getElementById('steps-container').style.display = 'none';
    });
}


function loadChargingStations() {
    fetch('/charging')
        .then(res => res.json())
        .then(data => {
            // Xóa các marker cũ nếu có
            chargingMarkers.forEach(marker => map.removeLayer(marker));
            chargingMarkers = [];

            data.forEach(station => {
                const marker = L.marker([station.lat, station.lon], {
                    icon: L.icon({
                        iconUrl: "/static/icon.png",
                        iconSize: [30, 30],
                        iconAnchor: [15, 30]
                    })
                }).addTo(map);
                marker.bindPopup("Trạm sạc ⚡<br>");
                chargingMarkers.push(marker);
            });
        })
        .catch(error => console.error('Error loading charging stations:', error));
}

// Hàm xác định địa chỉ
async function geocodeAddress() {
    const addressStart = document.getElementById('addressInputStart').value;
    const addressEnd = document.getElementById('addressInputEnd').value;

    if (!addressStart || !addressEnd) {
        alert("Vui lòng nhập cả điểm bắt đầu và điểm kết thúc!");
        return false;
    }

    try {
        const [startData, endData] = await Promise.all([
            fetch('/geocode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ address: addressStart })
            }).then(res => res.json()),

            fetch('/geocode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ address: addressEnd })
            }).then(res => res.json())
        ]);

        if (startData.error || endData.error) {
            alert(`Lỗi xác định địa chỉ: ${startData.error || endData.error}`);
            return false;
        }

        if (startData.lat && startData.lon && endData.lat && endData.lon) {
            currentStart = [startData.lat, startData.lon];
            currentEnd = [endData.lat, endData.lon];

            if (startMarker) map.removeLayer(startMarker);
            if (endMarker) map.removeLayer(endMarker);

            startMarker = L.marker(currentStart, {
                icon: L.icon({
                    iconUrl: "/static/start.png",
                    iconSize: [32, 32],
                    iconAnchor: [16, 32]
                })
            }).addTo(map).bindPopup("Điểm bắt đầu").openPopup();

            endMarker = L.marker(currentEnd, {
                icon: L.icon({
                    iconUrl: "/static/end.png",
                    iconSize: [32, 32],
                    iconAnchor: [16, 32]
                })
            }).addTo(map).bindPopup("Điểm kết thúc").openPopup();

            map.fitBounds([currentStart, currentEnd]);
            return true;
        } else {
            alert("Không tìm thấy một trong hai địa chỉ.");
            return false;
        }
    } catch (error) {
        console.error('Geocode error:', error);
        alert('Có lỗi xảy ra khi tìm địa chỉ: ' + error.message);
        return false;
    }
}

// Hàm hiển thị chi tiết lộ trình
function displayRouteDetails(routeData, algorithm) {
    const stepsContainer = document.getElementById('steps-container');
    const stepsList = document.getElementById('steps-list');

    // Hiển thị container
    stepsContainer.style.display = 'block';

    // Xóa nội dung cũ
    stepsList.innerHTML = '';

    // Hiển thị tổng quan lộ trình
    const totalDistance = routeData.steps.reduce((sum, step) => sum + (step.distance || 0), 0).toFixed(2);
    const chargingCount = routeData.steps.filter(step => step.is_charging).length;

    const summaryDiv = document.getElementById('summary');
    summaryDiv.innerHTML = `
        <div><strong>Thuật toán:</strong> <span class="algorithm-tag ${algorithm === 'A*' ? 'a-star-tag' : 'ucs-tag'}">${algorithm}</span></div>
        <div><strong>Tổng khoảng cách:</strong> ${totalDistance} mét</div>
        <div><strong>Số bước:</strong> ${routeData.steps.length}</div>
        <div><strong>Số lần sạc:</strong> ${chargingCount}</div>
    `;


    routeData.steps.forEach((step, index) => {
        const stepElement = document.createElement('div');
        stepElement.className = `step-item ${step.is_charging ? 'charging-step' : ''}`;

        // Tạo thanh pin
        const batteryPercent = Math.max(0, Math.min(100, step.battery));
        const batteryBar = `
            <div class="battery-display">
                <div class="battery-level" style="width:${batteryPercent}%"></div>
            </div>
            <div class="battery-text">${batteryPercent.toFixed(1)}%</div>
        `;

        let stepIcon = '➡️';
        let stepLabel = 'Di chuyển';
        if (index === 0) {
            stepIcon = "/static/start.png";
            stepLabel = 'Bắt đầu';
        } else if (index === routeData.steps.length - 1) {
            stepIcon = "/static/end.png";
            stepLabel = 'Kết thúc';
        } else if (step.is_charging) {
            stepIcon = "/static/icon.png";
            stepLabel = 'Sạc pin';
        }

        stepElement.innerHTML = `
            <div class="step-header">
                <span>${stepIcon}</span>
                <span>${stepLabel}</span>
            </div>
            <div class="step-distance">Khoảng cách: ${step.distance ? step.distance.toFixed(2) + 'm' : '--'}</div>
            ${batteryBar}
            ${step.is_charging ? '<div class="charging-note">Đã sạc pin</div>' : ''}
        `;

        stepsList.appendChild(stepElement);
    });
}

// Hàm tìm đường bằng UCS
function UCS() {
    if (!currentStart || !currentEnd) {
        alert("Vui lòng chọn điểm bắt đầu và kết thúc trước!");
        return;
    }

    console.log("Calling UCS with:", currentStart, currentEnd);

    fetch('/ucs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            start: currentStart,
            end: currentEnd
        })
    })
    .then(res => {
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
    })
    .then(data => {
        console.log("UCS response:", data);

        if (data.error) {
            alert("Lỗi: " + data.error);
            return;
        }

        if (routeLine) {
            map.removeLayer(routeLine);
        }

        if (data.route && data.route.length > 0) {

            routeLine = L.polyline(data.route, {
                color: '#2ecc71',
                weight: 5,
                opacity: 0.8
            }).addTo(map);

            map.fitBounds(routeLine.getBounds());

            // Hiển thị chi tiết lộ trình
            if (data.steps) {
                currentRouteDetails = data;
                displayRouteDetails(data, "UCS");
            }

            const successMsg = L.popup()
                .setLatLng([currentEnd[0], currentEnd[1]])
                .setContent("Tìm đường bằng UCS thành công!")
                .openOn(map);

            setTimeout(() => {
                map.closePopup(successMsg);
            }, 3000);
        } else {
            alert("Không tìm thấy đường đi!");
        }
    })
    .catch(error => {
        console.error("UCS Error:", error);
        alert("Lỗi khi tìm đường: " + error.message);
    });
}

// Hàm tìm đường bằng A*
function A_Star() {
    if (!currentStart || !currentEnd) {
        alert("Vui lòng chọn điểm bắt đầu và kết thúc trước!");
        return;
    }

    console.log("Calling A-Star with:", currentStart, currentEnd);

    fetch('/a_star', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            start: currentStart,
            end: currentEnd
        })
    })
    .then(res => {
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        return res.json();
    })
    .then(data => {
        console.log("A-Star response:", data);

        if (data.error) {
            alert("Lỗi: " + data.error);
            return;
        }

        if (routeLine) {
            map.removeLayer(routeLine);
        }

        if (data.route && data.route.length > 0) {
            routeLine = L.polyline(data.route, {
                color: '#3498db',
                weight: 5,
                opacity: 0.8
            }).addTo(map);

            map.fitBounds(routeLine.getBounds());

            if (data.steps) {
                currentRouteDetails = data;
                displayRouteDetails(data, "A*");
            }

            const successMsg = L.popup()
                .setLatLng([currentEnd[0], currentEnd[1]])
                .setContent("Tìm đường bằng A-Star thành công!")
                .openOn(map);

            setTimeout(() => {
                map.closePopup(successMsg);
            }, 3000);
        } else {
            alert("Không tìm thấy đường đi!");
        }
    })
    .catch(error => {
        console.error("A-Star Error:", error);
        alert("Lỗi khi tìm đường: " + error.message);
    });
}

// Khởi tạo ứng dụng khi trang được tải
document.addEventListener('DOMContentLoaded', () => {
    // Khởi tạo bản đồ
    initMap();

    // Thêm sự kiện cho các nút
    document.getElementById("a-star").addEventListener("click", async () => {
        if (await geocodeAddress()) {
            A_Star();
        }
    });

    document.getElementById("ucs").addEventListener("click", async () => {
        if (await geocodeAddress()) {
            UCS();
        }
    });

    // Cho phép nhấn Enter để tìm kiếm
    document.getElementById('addressInputStart').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            document.getElementById("a-star").click();
        }
    });

    document.getElementById('addressInputEnd').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            document.getElementById("ucs").click();
        }
    });

    // Thêm sự kiện khi thay đổi kích thước màn hình
    window.addEventListener('resize', () => {
        if (routeLine) {
            map.fitBounds(routeLine.getBounds());
        }
    });
});