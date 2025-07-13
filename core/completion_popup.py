"""Popup de conclusão com informações detalhadas de desempenho."""

import os
from datetime import datetime
from typing import Dict, Any, Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QFrame, QScrollArea, QWidget, QGridLayout
)


class CompletionPopup(QDialog):
    """Popup informativo de conclusão com métricas de performance detalhadas."""
    
    def __init__(self, performance_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.performance_data = performance_data
        self.init_ui()
        
        # Auto-close timer (optional)
        self.auto_close_timer = QTimer()
        self.auto_close_timer.setSingleShot(True)
        self.auto_close_timer.timeout.connect(self.accept)
    
    def init_ui(self):
        """Inicializa a interface do popup."""
        self.setWindowTitle("🎯 Transcrição Concluída - VoxSynopsis")
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint)
        self.setModal(True)
        self.resize(650, 500)
        
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header com ícone e título
        header_layout = self._create_header()
        main_layout.addLayout(header_layout)
        
        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # Grid de métricas principais
        metrics_grid = self._create_metrics_grid()
        main_layout.addWidget(metrics_grid)
        
        # Informações detalhadas (scrollable)
        details_widget = self._create_details_section()
        main_layout.addWidget(details_widget)
        
        # Botões de ação
        buttons_layout = self._create_buttons()
        main_layout.addLayout(buttons_layout)
        
        self.setLayout(main_layout)
        
        # Aplica estilos
        self._apply_styles()
    
    def _create_header(self) -> QHBoxLayout:
        """Cria o cabeçalho do popup."""
        header_layout = QHBoxLayout()
        
        # Ícone de sucesso
        icon_label = QLabel("🎯")
        icon_label.setStyleSheet("font-size: 32px;")
        header_layout.addWidget(icon_label)
        
        # Título e subtítulo
        title_layout = QVBoxLayout()
        
        title_label = QLabel("Transcrição Concluída com Sucesso!")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #57c93b;")
        title_layout.addWidget(title_label)
        
        subtitle_label = QLabel(f"Finalizado em {datetime.now().strftime('%H:%M:%S')}")
        subtitle_label.setStyleSheet("font-size: 12px; color: #aaa;")
        title_layout.addWidget(subtitle_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        return header_layout
    
    def _create_metrics_grid(self) -> QWidget:
        """Cria grid com métricas principais."""
        metrics_widget = QWidget()
        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        # Extrai dados principais
        total_files = self.performance_data.get('total_files', 0)
        successful_files = self.performance_data.get('successful_files', 0)
        failed_files = self.performance_data.get('failed_files', 0)
        processing_time = self.performance_data.get('total_processing_time', 0)
        success_rate = self.performance_data.get('success_rate', 0)
        
        # Calcula throughput
        throughput = successful_files / (processing_time / 60) if processing_time > 0 else 0
        
        # Define métricas para exibir (cores ajustadas para tema escuro)
        metrics = [
            ("📊 Total de Arquivos", str(total_files), "#0078d7"),
            ("✅ Processados", str(successful_files), "#57c93b"),
            ("❌ Falhas", str(failed_files), "#e74c3c" if failed_files > 0 else "#888"),
            ("⏱️ Tempo Total", self._format_duration(processing_time), "#f39c12"),
            ("📈 Taxa de Sucesso", f"{success_rate:.1f}%", "#57c93b"),
            ("🚀 Throughput", f"{throughput:.1f} arq/min", "#9b59b6")
        ]
        
        # Cria widgets para cada métrica
        for i, (label, value, color) in enumerate(metrics):
            row = i // 3
            col = (i % 3) * 2
            
            # Label da métrica
            metric_label = QLabel(label)
            metric_label.setStyleSheet("font-size: 11px; color: #aaa; font-weight: 500;")
            grid_layout.addWidget(metric_label, row * 2, col)
            
            # Valor da métrica
            value_label = QLabel(value)
            value_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
            grid_layout.addWidget(value_label, row * 2 + 1, col)
        
        metrics_widget.setLayout(grid_layout)
        return metrics_widget
    
    def _create_details_section(self) -> QScrollArea:
        """Cria seção com informações detalhadas."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)
        
        details_widget = QWidget()
        details_layout = QVBoxLayout()
        
        # Texto detalhado
        details_text = QTextEdit()
        details_text.setReadOnly(True)
        details_text.setMaximumHeight(180)
        
        # Gera conteúdo detalhado
        details_content = self._generate_details_content()
        details_text.setPlainText(details_content)
        
        details_layout.addWidget(details_text)
        details_widget.setLayout(details_layout)
        scroll_area.setWidget(details_widget)
        
        return scroll_area
    
    def _create_buttons(self) -> QHBoxLayout:
        """Cria botões de ação."""
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # Botão para visualizar relatório completo
        view_report_btn = QPushButton("📄 Ver Relatório Completo")
        view_report_btn.clicked.connect(self._show_full_report)
        view_report_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: #f0f0f0;
                border: 1px solid #0078d7;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: 500;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #106ebe;
                border: 1px solid #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        buttons_layout.addWidget(view_report_btn)
        
        # Botão OK
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        ok_button.setDefault(True)
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: #5c5c5c;
                color: #f0f0f0;
                border: 1px solid #666;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: 500;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #6c6c6c;
                border: 1px solid #777;
            }
            QPushButton:pressed {
                background-color: #4c4c4c;
            }
        """)
        buttons_layout.addWidget(ok_button)
        
        return buttons_layout
    
    def _generate_details_content(self) -> str:
        """Gera conteúdo detalhado para a seção de informações."""
        lines = []
        
        # Debug: Print available keys
        print(f"DEBUG: Performance data keys: {list(self.performance_data.keys())}")
        
        # Informações de timing
        start_time = self.performance_data.get('start_time', 'N/A')
        end_time = self.performance_data.get('end_time', 'N/A')
        
        if start_time != 'N/A':
            lines.append(f"🕐 Início: {start_time}")
        
        if end_time != 'N/A':
            lines.append(f"🕑 Fim: {end_time}")
        
        # Performance metrics
        processing_time = self.performance_data.get('total_processing_time', 0)
        if processing_time > 0:
            lines.append(f"⏱️ Tempo de Processamento: {self._format_duration(processing_time)}")
            
            avg_time = self.performance_data.get('average_time_per_file', 0)
            if avg_time > 0:
                lines.append(f"📊 Tempo Médio por Arquivo: {avg_time:.1f}s")
        
        # Audio duration and RTF
        audio_duration = self.performance_data.get('audio_duration_total', 0)
        if audio_duration > 0:
            lines.append(f"🎵 Duração Total de Áudio: {self._format_duration(audio_duration)}")
            rtf = audio_duration / processing_time if processing_time > 0 else 0
            lines.append(f"⚡ Fator Tempo Real (RTF): {rtf:.1f}x")
        
        # Speedup information
        speedup = self.performance_data.get('speedup', 0)
        if speedup > 1:
            lines.append(f"🚀 Speedup por Paralelização: {speedup:.1f}x")
        
        # Configuration summary - with debug
        model = self.performance_data.get('model_size', 'N/A')
        device = self.performance_data.get('device', 'N/A')
        compute_type = self.performance_data.get('compute_type', 'N/A')
        
        print(f"DEBUG: Model: {model}, Device: {device}, Compute: {compute_type}")
        
        lines.append(f"⚙️ Modelo: {model} | Dispositivo: {device}")
        if compute_type != 'N/A':
            lines.append(f"🔧 Tipo de Computação: {compute_type}")
        
        # Error details
        failed_files = self.performance_data.get('failed_files', 0)
        if failed_files > 0:
            lines.append(f"⚠️ {failed_files} arquivo(s) falharam - verifique o log para detalhes")
        
        return "\n".join(lines)
    
    def _format_duration(self, seconds: float) -> str:
        """Formata duração em formato legível."""
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
    
    def _apply_styles(self):
        """Aplica estilos gerais ao popup seguindo o tema da aplicação."""
        self.setStyleSheet("""
            QDialog {
                background-color: #3c3c3c;
                border: 1px solid #555;
                color: #f0f0f0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #d0d0d0;
            }
            QTextEdit {
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #3c3c3c;
                color: #f0f0f0;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                padding: 8px;
            }
            QScrollArea {
                border: none;
                background-color: #3c3c3c;
            }
            QFrame[frameShape="4"] {
                color: #555;
            }
        """)
    
    def _show_full_report(self):
        """Exibe o relatório completo em uma nova janela."""
        full_report = self.performance_data.get('full_report', 'Relatório completo não disponível.')
        
        from .report_viewer import ReportViewerDialog
        report_dialog = ReportViewerDialog(full_report, self)
        report_dialog.exec_()
    
    def show_with_auto_close(self, timeout_seconds: int = 10):
        """Exibe o popup com fechamento automático opcional."""
        self.auto_close_timer.start(timeout_seconds * 1000)
        self.exec_()
    
    @staticmethod
    def show_completion_popup(performance_data: Dict[str, Any], parent=None, auto_close: Optional[int] = None):
        """Método estático para exibir popup de conclusão."""
        popup = CompletionPopup(performance_data, parent)
        
        if auto_close:
            popup.show_with_auto_close(auto_close)
        else:
            popup.exec_()
        
        return popup