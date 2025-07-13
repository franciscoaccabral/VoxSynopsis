"""Visualizador de relatórios completos em janela separada."""

import os
from datetime import datetime
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTextEdit, 
    QPushButton, QLabel, QFileDialog, QMessageBox
)


class ReportViewerDialog(QDialog):
    """Dialog para visualização de relatórios completos com opções de exportação."""
    
    def __init__(self, report_content: str, parent=None):
        super().__init__(parent)
        self.report_content = report_content
        self.init_ui()
    
    def init_ui(self):
        """Inicializa a interface do visualizador."""
        self.setWindowTitle("📄 Relatório Completo de Transcrição - VoxSynopsis")
        self.setModal(True)
        self.resize(900, 700)
        
        # Layout principal
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header_layout = self._create_header()
        main_layout.addLayout(header_layout)
        
        # Área de texto do relatório
        self.report_text = QTextEdit()
        self.report_text.setReadOnly(True)
        self.report_text.setPlainText(self.report_content)
        
        # Configurar fonte monospace para melhor formatação
        font = QFont("Consolas", 10)
        if not font.exactMatch():
            font = QFont("Monaco", 10)
        if not font.exactMatch():
            font = QFont("Courier New", 10)
        self.report_text.setFont(font)
        
        main_layout.addWidget(self.report_text)
        
        # Botões de ação
        buttons_layout = self._create_buttons()
        main_layout.addLayout(buttons_layout)
        
        self.setLayout(main_layout)
        self._apply_styles()
    
    def _create_header(self) -> QHBoxLayout:
        """Cria o cabeçalho do visualizador."""
        header_layout = QHBoxLayout()
        
        # Título
        title_label = QLabel("📄 Relatório Completo de Transcrição")
        title_label.setStyleSheet("""
            font-size: 16px; 
            font-weight: bold; 
            color: #0078d7;
            padding: 5px 0px;
        """)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Timestamp
        timestamp_label = QLabel(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        timestamp_label.setStyleSheet("font-size: 11px; color: #aaa;")
        header_layout.addWidget(timestamp_label)
        
        return header_layout
    
    def _create_buttons(self) -> QHBoxLayout:
        """Cria botões de ação."""
        buttons_layout = QHBoxLayout()
        
        # Botão Copiar
        copy_button = QPushButton("📋 Copiar para Área de Transferência")
        copy_button.clicked.connect(self._copy_to_clipboard)
        copy_button.setStyleSheet(self._get_button_style("#607D8B"))
        buttons_layout.addWidget(copy_button)
        
        # Botão Salvar
        save_button = QPushButton("💾 Salvar como Arquivo")
        save_button.clicked.connect(self._save_to_file)
        save_button.setStyleSheet(self._get_button_style("#4CAF50"))
        buttons_layout.addWidget(save_button)
        
        buttons_layout.addStretch()
        
        # Botão Fechar
        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.accept)
        close_button.setDefault(True)
        close_button.setStyleSheet(self._get_button_style("#1976D2"))
        buttons_layout.addWidget(close_button)
        
        return buttons_layout
    
    def _get_button_style(self, color: str) -> str:
        """Retorna estilo para botões seguindo o tema da aplicação."""
        if color == "#4CAF50":  # Botão Salvar
            return """
                QPushButton {
                    background-color: #57c93b;
                    color: #f0f0f0;
                    border: 1px solid #57c93b;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: 500;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #4fb82f;
                    border: 1px solid #4fb82f;
                }
                QPushButton:pressed {
                    background-color: #3e9625;
                }
            """
        elif color == "#1976D2":  # Botão Fechar
            return """
                QPushButton {
                    background-color: #0078d7;
                    color: #f0f0f0;
                    border: 1px solid #0078d7;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: 500;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                    border: 1px solid #106ebe;
                }
                QPushButton:pressed {
                    background-color: #005a9e;
                }
            """
        else:  # Botão Copiar
            return """
                QPushButton {
                    background-color: #5c5c5c;
                    color: #f0f0f0;
                    border: 1px solid #666;
                    padding: 8px 16px;
                    border-radius: 4px;
                    font-weight: 500;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background-color: #6c6c6c;
                    border: 1px solid #777;
                }
                QPushButton:pressed {
                    background-color: #4c4c4c;
                }
            """
    
    
    def _copy_to_clipboard(self):
        """Copia o relatório para a área de transferência."""
        from PyQt5.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(self.report_content)
        
        QMessageBox.information(
            self,
            "Sucesso",
            "Relatório copiado para a área de transferência!",
            QMessageBox.Ok
        )
    
    def _save_to_file(self):
        """Salva o relatório em um arquivo."""
        # Sugere nome do arquivo baseado na data/hora
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suggested_name = f"relatorio_transcricao_{timestamp}.txt"
        
        # Abre dialog para salvar arquivo
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Relatório",
            suggested_name,
            "Arquivo de Texto (*.txt);;Todos os Arquivos (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.report_content)
                
                QMessageBox.information(
                    self,
                    "Sucesso",
                    f"Relatório salvo com sucesso em:\n{file_path}",
                    QMessageBox.Ok
                )
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erro",
                    f"Erro ao salvar o arquivo:\n{str(e)}",
                    QMessageBox.Ok
                )
    
    def _apply_styles(self):
        """Aplica estilos gerais ao dialog seguindo o tema da aplicação."""
        self.setStyleSheet("""
            QDialog {
                background-color: #3c3c3c;
                border: 1px solid #555;
                color: #f0f0f0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QTextEdit {
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #3c3c3c;
                color: #f0f0f0;
                padding: 10px;
                line-height: 1.4;
                font-family: 'Consolas', 'Monaco', monospace;
            }
            QLabel {
                color: #d0d0d0;
            }
        """)