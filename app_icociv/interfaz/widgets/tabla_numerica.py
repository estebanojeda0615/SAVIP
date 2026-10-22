"""Datos numéricos de tabla separados de display, metadatos y copia."""
import math
import re
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication,QTableView
from app_icociv.interfaz.widgets.modelo_tabla import ModeloTablaPandas


def numero_original(valor):
    if valor is None or isinstance(valor,bool):
        return None
    if isinstance(valor,str):
        texto=re.sub(r'\s*\((?:proyectado|estimado)\)\s*$','',valor.strip(),flags=re.I)
        texto=texto.removeprefix('$').removesuffix('%').strip()
        if ',' in texto:
            if not re.fullmatch(r'[+-]?(?:\d+|\d{1,3}(?:\.\d{3})+),\d+',texto):
                return None
            texto=texto.replace('.','').replace(',','.')
        elif not re.fullmatch(r'[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?',texto):
            return None
        valor=texto
    try:
        valor=float(valor)
        return valor if math.isfinite(valor) else None
    except (TypeError,ValueError,OverflowError):
        return None


def variacion_indice(inicial,final):
    inicial,final=numero_original(inicial),numero_original(final)
    if inicial is None or final is None or inicial==0:
        return None
    return numero_original(((final/inicial)-1)*100)


def texto_numero(valor,decimales=3):
    if valor is None:
        return ''
    if not decimales:
        # Fase 4I: enteros (p. ej. pesos COP) redondeados al alza en la mitad, no «al par».
        from decimal import Decimal, ROUND_HALF_UP
        return f"{int(Decimal(repr(float(valor))).quantize(Decimal('1'), rounding=ROUND_HALF_UP)):,}"
    texto=f'{valor:,.{decimales}f}'.rstrip('0').rstrip('.') if decimales else f'{valor:,.0f}'
    if texto in ('0','-0') and valor!=0:
        return f'{valor:.2e}'
    return '0' if texto=='-0' else texto


class ModeloTablaNumerica(ModeloTablaPandas):
    def __init__(self,decimales):
        super().__init__()
        self.decimales=decimales
        self.notas=[]

    def data(self,index,role=Qt.DisplayRole):
        if not index.isValid():
            return None
        columna=self._dataframe.columns[index.column()]
        if columna not in self.decimales:
            return super().data(index,role)
        valor=numero_original(self._dataframe.iat[index.row(),index.column()])
        if role==Qt.UserRole:
            return valor
        if role==Qt.DisplayRole:
            return texto_numero(valor,self.decimales[columna])
        if role==Qt.TextAlignmentRole:
            return Qt.AlignRight|Qt.AlignVCenter
        if role==Qt.ToolTipRole:
            nota=self.notas[index.row()] if index.row()<len(self.notas) else ''
            # Ayuda breve (hasta 6 decimales); el valor completo sigue en el dato y en «Ver detalle».
            texto='No disponible / no aplica' if valor is None else f'Valor original: {valor:,.6f}'.rstrip('0').rstrip('.')
            return texto+('\n'+nota if nota else '')
        return None


class TablaCopiable(QTableView):
    def pegar_en_celda(self):
        """Pega un único valor del portapapeles en la celda editable actual."""
        from PySide6.QtWidgets import QToolTip
        index=self.currentIndex();texto=QApplication.clipboard().text().strip('\r\n')
        if not index.isValid() or not (self.model().flags(index) & Qt.ItemIsEditable):
            return False
        if '\t' in texto or '\n' in texto:
            # Fase 4I-A: aviso breve NO modal junto a la celda; el valor anterior se conserva.
            QToolTip.showText(self.viewport().mapToGlobal(self.visualRect(index).bottomLeft()),
                              'Se recibió un rango de varias celdas; pegue un solo valor por celda.',self.viewport())
            return False
        return bool(self.model().setData(index,texto,Qt.EditRole))

    def keyPressEvent(self,event):
        if event.matches(QKeySequence.StandardKey.Paste) and self.state()!=QTableView.EditingState:
            self.pegar_en_celda();return
        if event.matches(QKeySequence.StandardKey.Copy):
            indices=self.selectedIndexes()
            if indices:
                celdas={}
                for index in indices:
                    valor=index.data(Qt.UserRole)
                    celdas[index.row(),index.column()]=str(valor) if valor is not None else str(index.data() or '')
                filas=sorted({i.row() for i in indices});columnas=sorted({i.column() for i in indices})
                QApplication.clipboard().setText('\n'.join('\t'.join(celdas.get((f,c),'') for c in columnas) for f in filas))
            return
        super().keyPressEvent(event)
