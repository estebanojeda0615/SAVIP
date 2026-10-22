"""Una barra contextual por módulo, con destino explícito y menú conservado."""
from PySide6.QtCore import QEvent,QSize,Qt
from PySide6.QtWidgets import QWidget,QVBoxLayout,QGridLayout,QLabel,QLayout,QPushButton,QMenu
from app_icociv.reportes.generador_reportes import esta_pdf_disponible,esta_docx_disponible


class BarraAccionesTablas(QWidget):
    def __init__(self,parent,tablas,conteo,exportable,detalle,eliminar,todo,exportar,editar=None):
        super().__init__(parent)
        self.setObjectName('barra_acciones_tablas')
        self.tablas=tablas;self.conteo=conteo;self.exportable=exportable;self.activa=None
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0)
        layout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)  # el mínimo lo da minimumSizeHint
        self.etiqueta=QLabel();self.etiqueta.setWordWrap(True);layout.addWidget(self.etiqueta)
        # Fase 4I-I: rejilla que se reacomoda al ancho (antes una fila fija de 5 botones exigía 672 px y
        # forzaba la barra horizontal de todo el módulo en media pantalla). Mismos botones y conexiones.
        self._rejilla=QGridLayout();self._rejilla.setContentsMargins(0,0,0,0);layout.addLayout(self._rejilla);self._columnas=0
        self.boton_detalle=QPushButton('Ver detalle');self.boton_eliminar=QPushButton('Eliminar seleccionado')
        self.boton_todo=QPushButton('Eliminar todo');self.boton_exportar=QPushButton('Exportar / informes')
        # Fase 4F: jerarquía visual (secundario / peligro / menú de exportación primario).
        self.boton_detalle.setObjectName('boton_secundario')
        self.boton_eliminar.setObjectName('boton_peligro');self.boton_todo.setObjectName('boton_peligro')
        for boton,accion in ((self.boton_detalle,detalle),(self.boton_eliminar,eliminar),(self.boton_todo,todo)):
            boton.clicked.connect(accion)
        # Fase 4G-B: «Editar actividad» solo existe si el módulo lo pide (ICOCIV); Empalme no cambia.
        self.boton_editar=None
        if editar is not None:
            self.boton_editar=QPushButton('Editar actividad');self.boton_editar.setObjectName('boton_secundario')
            self.boton_editar.setToolTip('Carga en la calculadora los datos de la actividad seleccionada para modificarla.')
            self.boton_editar.clicked.connect(editar)
        self._botones=[b for b in (self.boton_detalle,self.boton_editar,self.boton_eliminar,self.boton_todo,self.boton_exportar) if b is not None]
        for boton in self._botones:boton.setFocusPolicy(Qt.StrongFocus)
        self._reacomodar(len(self._botones))
        self.menu=QMenu(self.boton_exportar);self.acciones_exportacion={}
        self.disponibles={'xlsx':True,'pdf':esta_pdf_disponible(),'docx':esta_docx_disponible()}
        for extension,texto in (('xlsx','Archivo Excel (.xlsx)'),('pdf','Informe PDF (.pdf)'),('docx','Informe Word (.docx)')):
            accion=self.menu.addAction(texto)
            accion.triggered.connect(lambda checked=False,ext=extension:exportar(ext))
            self.acciones_exportacion[extension]=accion
        self.boton_exportar.setMenu(self.menu)
        for i,(tabla,nombre) in enumerate(tablas):
            tabla.installEventFilter(self);tabla.viewport().installEventFilter(self)
            tabla.selectionModel().selectionChanged.connect(lambda *args,n=i:self._seleccion(n))
            tabla.selectionModel().currentChanged.connect(lambda *args,n=i:self._seleccion(n))
            tabla.model().modelReset.connect(self.actualizar)
        self.actualizar()

    def _reacomodar(self,columnas):
        if columnas==self._columnas:return
        self._columnas=columnas
        for boton in self._botones:self._rejilla.removeWidget(boton)
        for i,boton in enumerate(self._botones):self._rejilla.addWidget(boton,i//columnas,i%columnas)
        for c in range(len(self._botones)+1):self._rejilla.setColumnStretch(c,0)
        self._rejilla.setColumnStretch(columnas,1)  # sobrante a la derecha, como el stretch de la fila original

    def _columnas_que_caben(self,ancho):
        espacio=max(self._rejilla.horizontalSpacing(),0);usado=0
        for n,boton in enumerate(self._botones,1):
            usado+=boton.sizeHint().width()+(espacio if n>1 else 0)
            if usado>ancho:return max(1,n-1)
        return len(self._botones)

    def minimumSizeHint(self):  # el mínimo es el del botón más ancho: la rejilla se reacomoda por debajo
        base=super().minimumSizeHint()
        return QSize(max(b.sizeHint().width() for b in self._botones),base.height())

    def resizeEvent(self,event):
        super().resizeEvent(event)
        self._reacomodar(self._columnas_que_caben(self.contentsRect().width()))

    def eventFilter(self,obj,event):
        if event.type() in (QEvent.FocusIn,QEvent.MouseButtonPress):
            for i,(tabla,_) in enumerate(self.tablas):
                if obj is tabla or obj is tabla.viewport():self.activa=i;self.actualizar();break
        return super().eventFilter(obj,event)

    def _seleccion(self,i):
        tabla=self.tablas[i][0]
        if tabla.selectionModel().hasSelection() or tabla.hasFocus():self.activa=i
        self.actualizar()

    @property
    def nombre(self):
        return self.tablas[self.activa][1] if self.activa is not None else 'sin selección explícita'

    def indice(self):
        if self.activa is None:return None
        tabla=self.tablas[self.activa][0]
        if len({index.row() for index in tabla.selectionModel().selectedIndexes()})>1:return None
        seleccion=tabla.selectionModel().selectedRows()
        index=seleccion[0] if seleccion else tabla.currentIndex()
        return index.row() if index.isValid() else None

    def actualizar(self):
        self.etiqueta.setText('Tabla activa: '+self.nombre)
        seleccionado=self.indice() is not None
        self.boton_detalle.setEnabled(seleccionado);self.boton_eliminar.setEnabled(seleccionado)
        if self.boton_editar is not None:self.boton_editar.setEnabled(seleccionado and self.activa==len(self.tablas)-1)
        self.boton_todo.setEnabled(self.activa is not None and self.conteo(self.activa)>0)
        self.boton_exportar.setEnabled(bool(self.exportable()))
        for ext,accion in self.acciones_exportacion.items():accion.setEnabled(bool(self.exportable()) and self.disponibles[ext])
        self.boton_detalle.setToolTip('Seleccione una fila de la tabla activa.')
        self.boton_eliminar.setToolTip('Elimina solo el registro seleccionado de la tabla activa.')
        self.boton_todo.setToolTip('Requiere confirmación del destino y alcance.')
        self.boton_exportar.setToolTip('Exporta el módulo completo; el filtro visual no limita los registros.')
