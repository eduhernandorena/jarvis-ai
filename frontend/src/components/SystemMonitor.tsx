import React, { useState, useEffect } from 'react';
import { Activity, Cpu, HardDrive, Zap } from 'lucide-react';

interface Stats {
  cpu_usage: number;
  ram_usage: number;
  disk_usage: number;
  uptime: string;
}

export function SystemMonitor({ backendUrl }: { backendUrl: string }) {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch(`${backendUrl}/api/stats`);
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch (e) {
        // Silencioso se falhar
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, 5000);
    return () => clearInterval(interval);
  }, [backendUrl]);

  if (!stats) return null;

  return (
    <div className="system-monitor-hud">
      <div className="stat-item">
        <Cpu size={12} />
        <span>CPU: {stats.cpu_usage}%</span>
      </div>
      <div className="stat-item">
        <Activity size={12} />
        <span>RAM: {stats.ram_usage}%</span>
      </div>
      <div className="stat-item">
        <HardDrive size={12} />
        <span>DSK: {stats.disk_usage}%</span>
      </div>
      <div className="stat-item uptime">
        <Zap size={12} />
        <span>{stats.uptime}</span>
      </div>
    </div>
  );
}
