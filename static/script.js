// Khai báo biến toàn cục
let map;
let startMarker = null;
let endMarker = null;
let routeLine = null;
let currentStart = null;
let currentEnd = null;

// Hàm khởi tạo bản đồ
function initMap() {
    map = L.map('map').setView([10.7769, 106.7009], 13);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '© OpenStreetMap'
    }).addTo(map);
    
    loadChargingStations();
}

// Hàm tải trạm sạc
function loadChargingStations() {
    fetch('/charging')
        .then(res => res.json())
        .then(data => {
            data.forEach(station => {
                const marker = L.marker([station.lat, station.lon], {
                    icon: L.icon({
                        iconUrl: "/static/icon.png",
                        iconSize: [30, 30]
                    })
                }).addTo(map);
                marker.bindPopup("Trạm sạc ⚡<br>");
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

            startMarker = L.marker(currentStart).addTo(map)
                .bindPopup("Điểm bắt đầu").openPopup();
                
            endMarker = L.marker(currentEnd).addTo(map)
                .bindPopup("Điểm kết thúc").openPopup();

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
                color: 'blue', 
                weight: 5 
            }).addTo(map);
            
            map.fitBounds(routeLine.getBounds());
            alert("Tìm đường bằng A-Star thành công!");
        } else {
            alert("Không tìm thấy đường đi!");
        }
    })
    .catch(error => {
        console.error("A-Star Error:", error);
        alert("Lỗi khi tìm đường: " + error.message);
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
                color: 'green', 
                weight: 5 
            }).addTo(map);
            
            map.fitBounds(routeLine.getBounds());
            alert("Tìm đường bằng UCS thành công!");
        } else {
            alert("Không tìm thấy đường đi!");
        }
    })
    .catch(error => {
        console.error("UCS Error:", error);
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
});