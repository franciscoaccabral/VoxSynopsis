"""Precise timestamp management for phase-by-phase performance analysis."""

import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class TimestampManager:
    """Manage precise timestamps for transcription phases and analysis."""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.current_session: Optional[str] = None
        self.active_phases: Dict[str, Dict[str, Any]] = {}
    
    def start_session(self, session_name: str = "transcription") -> None:
        """Start a new timestamp session."""
        current_time = time.time()
        current_dt = datetime.now(timezone.utc)
        
        self.current_session = session_name
        self.sessions[session_name] = {
            'start_timestamp': current_time,
            'start_datetime': current_dt.isoformat(),
            'start_formatted': current_dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'phases': {},
            'completed': False
        }
        self.active_phases.clear()
    
    def start_phase(self, phase_name: str) -> None:
        """Start timing a specific phase."""
        if not self.current_session:
            raise ValueError("No active session. Call start_session() first.")
        
        current_time = time.time()
        current_dt = datetime.now(timezone.utc)
        
        phase_data = {
            'start_timestamp': current_time,
            'start_datetime': current_dt.isoformat(),
            'start_formatted': current_dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'completed': False
        }
        
        self.active_phases[phase_name] = phase_data
        self.sessions[self.current_session]['phases'][phase_name] = phase_data
    
    def end_phase(self, phase_name: str) -> float:
        """End timing a phase and return its duration."""
        if phase_name not in self.active_phases:
            raise ValueError(f"Phase '{phase_name}' was not started or already ended.")
        
        current_time = time.time()
        current_dt = datetime.now(timezone.utc)
        
        phase_data = self.active_phases[phase_name]
        duration = current_time - phase_data['start_timestamp']
        
        # Update phase data
        phase_data.update({
            'end_timestamp': current_time,
            'end_datetime': current_dt.isoformat(),
            'end_formatted': current_dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'duration_seconds': duration,
            'duration_formatted': self._format_duration(duration),
            'completed': True
        })
        
        # Remove from active phases
        del self.active_phases[phase_name]
        
        return duration
    
    def end_session(self, session_name: Optional[str] = None) -> Dict[str, Any]:
        """End the current session and return summary."""
        session_key = session_name or self.current_session
        if not session_key or session_key not in self.sessions:
            raise ValueError("No active session to end.")
        
        current_time = time.time()
        current_dt = datetime.now(timezone.utc)
        
        session_data = self.sessions[session_key]
        total_duration = current_time - session_data['start_timestamp']
        
        # Update session data
        session_data.update({
            'end_timestamp': current_time,
            'end_datetime': current_dt.isoformat(),
            'end_formatted': current_dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'total_duration_seconds': total_duration,
            'total_duration_formatted': self._format_duration(total_duration),
            'completed': True
        })
        
        # End any remaining active phases
        for phase_name in list(self.active_phases.keys()):
            self.end_phase(phase_name)
        
        self.current_session = None
        return session_data
    
    def get_session_summary(self, session_name: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive session timing summary."""
        session_key = session_name or self.current_session
        if not session_key or session_key not in self.sessions:
            return {'error': 'Session not found'}
        
        session_data = self.sessions[session_key]
        
        # Calculate phase statistics
        completed_phases = {
            name: data for name, data in session_data['phases'].items() 
            if data.get('completed', False)
        }
        
        phase_stats = {}
        total_phase_time = 0
        
        for phase_name, phase_data in completed_phases.items():
            duration = phase_data['duration_seconds']
            total_phase_time += duration
            phase_stats[phase_name] = {
                'duration_seconds': duration,
                'duration_formatted': phase_data['duration_formatted'],
                'start_time': phase_data['start_formatted'],
                'end_time': phase_data['end_formatted']
            }
        
        # Calculate overhead (untracked time)
        session_duration = session_data.get('total_duration_seconds', 0)
        overhead_seconds = max(0, session_duration - total_phase_time)
        overhead_percentage = (overhead_seconds / session_duration * 100) if session_duration > 0 else 0
        
        return {
            'session_name': session_key,
            'start_time': session_data['start_formatted'],
            'end_time': session_data.get('end_formatted'),
            'total_duration_seconds': session_duration,
            'total_duration_formatted': session_data.get('total_duration_formatted'),
            'completed_phases': len(completed_phases),
            'phase_breakdown': phase_stats,
            'overhead_seconds': overhead_seconds,
            'overhead_percentage': round(overhead_percentage, 1),
            'completed': session_data.get('completed', False)
        }
    
    def get_timing_report(self, session_name: Optional[str] = None) -> str:
        """Generate formatted timing report."""
        summary = self.get_session_summary(session_name)
        
        if 'error' in summary:
            return f"❌ Error: {summary['error']}"
        
        report_lines = [
            "⏰ ANÁLISE TEMPORAL DETALHADA:",
            f"   📅 Sessão: {summary['session_name']}",
            f"   🕐 Início: {summary['start_time']}",
        ]
        
        if summary['completed']:
            report_lines.extend([
                f"   🕑 Fim: {summary['end_time']}",
                f"   ⏱️  Duração Total: {summary['total_duration_formatted']} ({summary['total_duration_seconds']:.1f}s)"
            ])
        else:
            current_duration = time.time() - self.sessions[summary['session_name']]['start_timestamp']
            report_lines.append(f"   ⏱️  Duração Atual: {self._format_duration(current_duration)} (em andamento)")
        
        # Phase breakdown
        if summary['phase_breakdown']:
            report_lines.append("\n📊 BREAKDOWN POR FASE:")
            
            total_seconds = summary['total_duration_seconds']
            for phase_name, phase_data in summary['phase_breakdown'].items():
                duration_s = phase_data['duration_seconds']
                percentage = (duration_s / total_seconds * 100) if total_seconds > 0 else 0
                
                report_lines.append(
                    f"   • {phase_name}: {phase_data['duration_formatted']} ({percentage:.1f}%)"
                )
            
            # Show overhead if significant
            if summary['overhead_percentage'] > 1:
                report_lines.append(
                    f"   • overhead/outros: {self._format_duration(summary['overhead_seconds'])} "
                    f"({summary['overhead_percentage']:.1f}%)"
                )
        
        # Performance insights
        if summary['completed'] and summary['phase_breakdown']:
            report_lines.append("\n🔍 ANÁLISE DE PERFORMANCE:")
            
            phase_times = [p['duration_seconds'] for p in summary['phase_breakdown'].values()]
            if phase_times:
                longest_phase = max(summary['phase_breakdown'].items(), key=lambda x: x[1]['duration_seconds'])
                report_lines.append(f"   • Fase mais lenta: {longest_phase[0]} ({longest_phase[1]['duration_formatted']})")
                
                if summary['overhead_percentage'] > 10:
                    report_lines.append(f"   ⚠️  Alto overhead detectado: {summary['overhead_percentage']:.1f}%")
                else:
                    report_lines.append(f"   ✅ Overhead controlado: {summary['overhead_percentage']:.1f}%")
        
        return "\n".join(report_lines)
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds:.1f}s"
        else:
            hours = int(seconds // 3600)
            remaining_minutes = int((seconds % 3600) // 60)
            remaining_seconds = seconds % 60
            return f"{hours}h {remaining_minutes}m {remaining_seconds:.1f}s"
    
    def add_checkpoint(self, checkpoint_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a timing checkpoint without ending current phase."""
        if not self.current_session:
            return
        
        current_time = time.time()
        current_dt = datetime.now(timezone.utc)
        
        if 'checkpoints' not in self.sessions[self.current_session]:
            self.sessions[self.current_session]['checkpoints'] = {}
        
        self.sessions[self.current_session]['checkpoints'][checkpoint_name] = {
            'timestamp': current_time,
            'datetime': current_dt.isoformat(),
            'formatted': current_dt.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'metadata': metadata or {}
        }
    
    def get_phase_duration(self, phase_name: str, session_name: Optional[str] = None) -> Optional[float]:
        """Get duration of a specific phase."""
        session_key = session_name or self.current_session
        if not session_key or session_key not in self.sessions:
            return None
        
        phases = self.sessions[session_key]['phases']
        if phase_name not in phases or not phases[phase_name].get('completed'):
            return None
        
        return phases[phase_name]['duration_seconds']
    
    def is_phase_active(self, phase_name: str) -> bool:
        """Check if a phase is currently active."""
        return phase_name in self.active_phases