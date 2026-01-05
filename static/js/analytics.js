        // Chart.js 설정
        Chart.defaults.color = '#94a3b8';
        Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';
        Chart.defaults.font.family = 'Inter, sans-serif';

        {% if stats.total_analyses > 0 %}

        // 시간대별 차트
        const hourlyCtx = document.getElementById('hourlyChart');
        if (hourlyCtx) {
            const hourlyData = {{ stats.hourly_stats|tojson }};
            const hours = Array.from({length: 24}, (_, i) => String(i).padStart(2, '0'));
            const counts = hours.map(h => hourlyData[h] || 0);

            new Chart(hourlyCtx, {
                type: 'bar',
                data: {
                    labels: hours.map(h => h + '시'),
                    datasets: [{
                        label: '분석 횟수',
                        data: counts,
                        backgroundColor: counts.map(c => 
                            c > 0 ? 'rgba(102, 126, 234, 0.8)' : 'rgba(102, 126, 234, 0.2)'
                        ),
                        borderColor: counts.map(c => 
                            c > 0 ? 'rgba(102, 126, 234, 1)' : 'rgba(102, 126, 234, 0.4)'
                        ),
                        borderWidth: 2,
                        borderRadius: 10,
                        hoverBackgroundColor: 'rgba(102, 126, 234, 1)',
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 1500,
                        easing: 'easeInOutQuart'
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(15, 23, 42, 0.95)',
                            titleColor: '#fff',
                            bodyColor: '#94a3b8',
                            borderColor: 'rgba(102, 126, 234, 0.5)',
                            borderWidth: 1,
                            padding: 12,
                            displayColors: false,
                            callbacks: {
                                title: (items) => items[0].label,
                                label: (item) => `${item.raw}회 분석`
                            }
                        }
                    },
                    scales: {
                        y: { 
                            beginAtZero: true,
                            grace: '10%',
                            suggestedMax: 10,
                            grid: { 
                                color: 'rgba(255, 255, 255, 0.05)',
                                drawBorder: false
                            },
                            ticks: {
                                stepSize: 1,
                                precision: 0,
                                color: '#94a3b8'
                            }
                        },
                        x: { 
                            grid: { display: false },
                            ticks: { color: '#94a3b8' }
                        }
                    }
                }
            });
        }

        // 일별 추이 차트
        const dailyCtx = document.getElementById('dailyChart');
        if (dailyCtx) {
            const dailyData = {{ stats.daily_stats|tojson }};
            const sortedDates = Object.keys(dailyData).sort();
            const labels = sortedDates.map(d => {
                const date = new Date(d);
                return (date.getMonth() + 1) + '/' + date.getDate();
            });
            const values = sortedDates.map(d => dailyData[d]);

            new Chart(dailyCtx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '일별 분석',
                        data: values,
                        borderColor: 'rgba(102, 126, 234, 1)',
                        backgroundColor: (context) => {
                            const ctx = context.chart.ctx;
                            const gradient = ctx.createLinearGradient(0, 0, 0, 300);
                            gradient.addColorStop(0, 'rgba(102, 126, 234, 0.3)');
                            gradient.addColorStop(1, 'rgba(102, 126, 234, 0)');
                            return gradient;
                        },
                        borderWidth: 3,
                        fill: true,
                        tension: 0.4,
                        pointRadius: 5,
                        pointHoverRadius: 8,
                        pointBackgroundColor: '#667eea',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: '#667eea',
                        pointHoverBorderWidth: 3,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 2000,
                        easing: 'easeInOutQuart'
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(15, 23, 42, 0.95)',
                            titleColor: '#fff',
                            bodyColor: '#94a3b8',
                            borderColor: 'rgba(102, 126, 234, 0.5)',
                            borderWidth: 1,
                            padding: 12,
                            displayColors: false,
                            callbacks: {
                                label: (item) => `${item.raw}회 분석`
                            }
                        }
                    },
                    scales: {
                        y: { 
                            beginAtZero: true,
                            grace: '10%',
                            suggestedMax: 10,
                            grid: { 
                                color: 'rgba(255, 255, 255, 0.05)',
                                drawBorder: false
                            },
                            ticks: {
                                stepSize: 1,
                                precision: 0,
                                color: '#94a3b8'
                            }
                        },
                        x: { 
                            grid: { 
                                color: 'rgba(255, 255, 255, 0.05)',
                                drawBorder: false
                            },
                            ticks: { 
                                color: '#94a3b8',
                                maxTicksLimit: 15
                            }
                        }
                    }
                }
            });
        }

        // 플랫폼 분포 차트
        {% if stats.top_blog_domains %}
        const platformCtx = document.getElementById('platformChart');
        if (platformCtx) {
            const platforms = {{ stats.top_blog_domains|tojson }};
            
            new Chart(platformCtx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(platforms),
                    datasets: [{
                        data: Object.values(platforms),
                        backgroundColor: [
                            'rgba(102, 126, 234, 0.9)',
                            'rgba(236, 72, 153, 0.9)',
                            'rgba(245, 158, 11, 0.9)',
                            'rgba(16, 185, 129, 0.9)',
                        ],
                        borderWidth: 3,
                        borderColor: 'rgba(15, 23, 42, 0.5)',
                        hoverBorderColor: '#fff',
                        hoverBorderWidth: 4,
                        hoverOffset: 15,
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 1500,
                        easing: 'easeInOutQuart'
                    },
                    layout: {
                        padding: {
                            top: 30,
                            bottom: 10,
                            left: 20,
                            right: 20
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 20,
                                font: { 
                                    size: 14,
                                    family: 'Inter'
                                },
                                color: '#94a3b8',
                                usePointStyle: true,
                                pointStyle: 'circle'
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(15, 23, 42, 0.95)',
                            titleColor: '#fff',
                            bodyColor: '#94a3b8',
                            borderColor: 'rgba(102, 126, 234, 0.5)',
                            borderWidth: 1,
                            padding: 12,
                            callbacks: {
                                label: (item) => {
                                    const value = item.raw;
                                    const total = item.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${item.label}: ${value}회 (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
        }
        {% endif %}

        // 💬 댓글 복사 & 블로그 이동 차트
        const engagementCtx = document.getElementById('engagementChart');
        if (engagementCtx) {
            const dailyCopies = {{ stats.daily_comment_copies|tojson }};
            const dailyVisits = {{ stats.daily_blog_visits|tojson }};
            const sortedDates = Object.keys(dailyCopies).sort();
            const labels = sortedDates.map(d => {
                const date = new Date(d);
                return (date.getMonth() + 1) + '/' + date.getDate();
            });
            const copiesData = sortedDates.map(d => dailyCopies[d] || 0);
            const visitsData = sortedDates.map(d => dailyVisits[d] || 0);

            new Chart(engagementCtx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: '댓글 복사',
                            data: copiesData,
                            borderColor: 'rgba(16, 185, 129, 1)',
                            backgroundColor: 'rgba(16, 185, 129, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 4,
                            pointHoverRadius: 7,
                            pointBackgroundColor: '#10b981',
                            pointBorderColor: '#fff',
                            pointBorderWidth: 2,
                        },
                        {
                            label: '블로그 이동',
                            data: visitsData,
                            borderColor: 'rgba(245, 158, 11, 1)',
                            backgroundColor: 'rgba(245, 158, 11, 0.1)',
                            borderWidth: 3,
                            fill: true,
                            tension: 0.4,
                            pointRadius: 4,
                            pointHoverRadius: 7,
                            pointBackgroundColor: '#f59e0b',
                            pointBorderColor: '#fff',
                            pointBorderWidth: 2,
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 2000,
                        easing: 'easeInOutQuart'
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top',
                            labels: {
                                padding: 15,
                                font: { size: 13, family: 'Inter' },
                                color: '#94a3b8',
                                usePointStyle: true,
                                pointStyle: 'circle'
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(15, 23, 42, 0.95)',
                            titleColor: '#fff',
                            bodyColor: '#94a3b8',
                            borderColor: 'rgba(102, 126, 234, 0.5)',
                            borderWidth: 1,
                            padding: 12,
                            displayColors: true,
                            callbacks: {
                                label: (item) => `${item.dataset.label}: ${item.raw}회`
                            }
                        }
                    },
                    scales: {
                        y: { 
                            beginAtZero: true,
                            grace: '10%',
                            suggestedMax: 10,
                            grid: { 
                                color: 'rgba(255, 255, 255, 0.05)',
                                drawBorder: false
                            },
                            ticks: {
                                stepSize: 1,
                                precision: 0,
                                color: '#94a3b8'
                            }
                        },
                        x: { 
                            grid: { 
                                color: 'rgba(255, 255, 255, 0.05)',
                                drawBorder: false
                            },
                            ticks: { 
                                color: '#94a3b8',
                                maxTicksLimit: 15
                            }
                        }
                    }
                }
            });
        }

        // 👥 방문자 통계 차트
        const visitorCtx = document.getElementById('visitorChart');
        if (visitorCtx) {
            const dailyViews = {{ stats.daily_page_views|tojson }};
            const sortedDates = Object.keys(dailyViews).sort();
            const labels = sortedDates.map(d => {
                const date = new Date(d);
                return (date.getMonth() + 1) + '/' + date.getDate();
            });
            const viewsData = sortedDates.map(d => dailyViews[d] || 0);

            new Chart(visitorCtx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '페이지뷰',
                        data: viewsData,
                        backgroundColor: viewsData.map(v => 
                            v > 0 ? 'rgba(139, 92, 246, 0.8)' : 'rgba(139, 92, 246, 0.2)'
                        ),
                        borderColor: viewsData.map(v => 
                            v > 0 ? 'rgba(139, 92, 246, 1)' : 'rgba(139, 92, 246, 0.4)'
                        ),
                        borderWidth: 2,
                        borderRadius: 8,
                        hoverBackgroundColor: 'rgba(139, 92, 246, 1)',
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 1500,
                        easing: 'easeInOutQuart'
                    },
                    interaction: {
                        intersect: false,
                        mode: 'index'
                    },
                    plugins: {
                        legend: { display: false },
                        tooltip: {
                            backgroundColor: 'rgba(15, 23, 42, 0.95)',
                            titleColor: '#fff',
                            bodyColor: '#94a3b8',
                            borderColor: 'rgba(139, 92, 246, 0.5)',
                            borderWidth: 1,
                            padding: 12,
                            displayColors: false,
                            callbacks: {
                                label: (item) => `${item.raw}회 방문`
                            }
                        }
                    },
                    scales: {
                        y: { 
                            beginAtZero: true,
                            grace: '10%',
                            suggestedMax: 10,
                            grid: { 
                                color: 'rgba(255, 255, 255, 0.05)',
                                drawBorder: false
                            },
                            ticks: {
                                stepSize: 1,
                                precision: 0,
                                color: '#94a3b8'
                            }
                        },
                        x: { 
                            grid: { display: false },
                            ticks: { 
                                color: '#94a3b8',
                                maxTicksLimit: 15
                            }
                        }
                    }
                }
            });
        }

        // 💬 피드백은 심플 카드로 표시 (차트 제거)

        {% endif %}

        // 페이지 애니메이션
        document.addEventListener('DOMContentLoaded', () => {
            const cards = document.querySelectorAll('.glass-card');
            cards.forEach((card, index) => {
                card.style.animationDelay = `${index * 0.1}s`;
            });
        });

        // 퍼널 애니메이션
        const funnelSteps = document.querySelectorAll('.funnel-step');
        funnelSteps.forEach((step, index) => {
            const count = step.querySelector('.funnel-count').textContent;
            if (count !== '-') {
                const maxCount = {{ stats.month_analyses if stats.month_analyses > 0 else 1 }};
                const percentage = (parseInt(count) / maxCount) * 100;
                step.style.setProperty('--funnel-width', percentage + '%');
                setTimeout(() => {
                    step.querySelector('::before').style.width = 'var(--funnel-width)';
                }, index * 200);
            }
        });

        // 🌐 브라우저 분포 차트
        {% if stats.browser_stats %}
        const browserCtx = document.getElementById('browserChart');
        if (browserCtx) {
            const browsers = {{ stats.browser_stats|tojson }};
            
            new Chart(browserCtx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(browsers),
                    datasets: [{
                        data: Object.values(browsers),
                        backgroundColor: [
                            'rgba(66, 153, 225, 0.9)',  // Chrome - Blue
                            'rgba(102, 126, 234, 0.9)', // Safari - Purple
                            'rgba(72, 187, 120, 0.9)',  // Edge - Green
                            'rgba(245, 158, 11, 0.9)',  // Firefox - Orange
                            'rgba(156, 163, 175, 0.9)'  // Other - Gray
                        ],
                        borderWidth: 3,
                        borderColor: 'rgba(15, 23, 42, 0.5)',
                        hoverBorderColor: '#fff',
                        hoverBorderWidth: 4,
                        hoverOffset: 15
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 1500,
                        easing: 'easeInOutQuart'
                    },
                    layout: {
                        padding: {
                            top: 30,
                            bottom: 10,
                            left: 20,
                            right: 20
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 20,
                                font: { size: 14, family: 'Inter' },
                                color: '#94a3b8',
                                usePointStyle: true,
                                pointStyle: 'circle'
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(15, 23, 42, 0.95)',
                            titleColor: '#fff',
                            bodyColor: '#94a3b8',
                            borderColor: 'rgba(102, 126, 234, 0.5)',
                            borderWidth: 1,
                            padding: 12,
                            callbacks: {
                                label: (item) => {
                                    const value = item.raw;
                                    const total = item.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${item.label}: ${value}명 (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
        }
        {% endif %}

        // 📱 디바이스 분포 차트
        {% if stats.device_stats %}
        const deviceCtx = document.getElementById('deviceChart');
        if (deviceCtx) {
            const devices = {{ stats.device_stats|tojson }};
            
            new Chart(deviceCtx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(devices),
                    datasets: [{
                        data: Object.values(devices),
                        backgroundColor: [
                            'rgba(139, 92, 246, 0.9)',  // Desktop - Purple
                            'rgba(236, 72, 153, 0.9)',  // Mobile - Pink
                            'rgba(251, 191, 36, 0.9)'   // Tablet - Yellow
                        ],
                        borderWidth: 3,
                        borderColor: 'rgba(15, 23, 42, 0.5)',
                        hoverBorderColor: '#fff',
                        hoverBorderWidth: 4,
                        hoverOffset: 15
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 1500,
                        easing: 'easeInOutQuart'
                    },
                    layout: {
                        padding: {
                            top: 30,
                            bottom: 10,
                            left: 20,
                            right: 20
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 20,
                                font: { size: 14, family: 'Inter' },
                                color: '#94a3b8',
                                usePointStyle: true,
                                pointStyle: 'circle'
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(15, 23, 42, 0.95)',
                            titleColor: '#fff',
                            bodyColor: '#94a3b8',
                            borderColor: 'rgba(236, 72, 153, 0.5)',
                            borderWidth: 1,
                            padding: 12,
                            callbacks: {
                                label: (item) => {
                                    const value = item.raw;
                                    const total = item.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${item.label}: ${value}명 (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
        }
        {% endif %}

        // 💻 OS 분포 차트
        {% if stats.os_stats %}
        const osCtx = document.getElementById('osChart');
        if (osCtx) {
            const osList = {{ stats.os_stats|tojson }};
            
            new Chart(osCtx, {
                type: 'doughnut',
                data: {
                    labels: Object.keys(osList),
                    datasets: [{
                        data: Object.values(osList),
                        backgroundColor: [
                            'rgba(59, 130, 246, 0.9)',   // Windows - Blue
                            'rgba(156, 163, 175, 0.9)',  // macOS - Gray
                            'rgba(251, 146, 60, 0.9)',   // iOS - Orange
                            'rgba(34, 197, 94, 0.9)',    // Android - Green
                            'rgba(245, 158, 11, 0.9)',   // Linux - Amber
                            'rgba(168, 85, 247, 0.9)'    // Other - Purple
                        ],
                        borderWidth: 3,
                        borderColor: 'rgba(15, 23, 42, 0.5)',
                        hoverBorderColor: '#fff',
                        hoverBorderWidth: 4,
                        hoverOffset: 15
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 1500,
                        easing: 'easeInOutQuart'
                    },
                    layout: {
                        padding: {
                            top: 30,
                            bottom: 10,
                            left: 20,
                            right: 20
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'bottom',
                            labels: {
                                padding: 20,
                                font: { size: 14, family: 'Inter' },
                                color: '#94a3b8',
                                usePointStyle: true,
                                pointStyle: 'circle'
                            }
                        },
                        tooltip: {
                            backgroundColor: 'rgba(15, 23, 42, 0.95)',
                            titleColor: '#fff',
                            bodyColor: '#94a3b8',
                            borderColor: 'rgba(34, 197, 94, 0.5)',
                            borderWidth: 1,
                            padding: 12,
                            callbacks: {
                                label: (item) => {
                                    const value = item.raw;
                                    const total = item.dataset.data.reduce((a, b) => a + b, 0);
                                    const percentage = ((value / total) * 100).toFixed(1);
                                    return `${item.label}: ${value}명 (${percentage}%)`;
                                }
                            }
                        }
                    }
                }
            });
        }
        {% endif %}

        console.log('📊 Repost Analytics Dashboard Pro loaded');
