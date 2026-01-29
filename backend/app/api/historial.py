"""
RF9. Historial de Rutas: listado de pedidos con ruta, conductor, vehículo y fecha de entrega realizada.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date
from app.database import get_db
from app.models.pedido import Pedido
from app.models.ruta import Ruta, RutaParada, EstadoParada, TipoOperacion
from app.models.conductor import Conductor
from app.models.vehiculo import Vehiculo
from app.models.usuario import Usuario
from app.api.dependencies import get_current_user
import io
import csv

router = APIRouter(prefix="/historial", tags=["historial"])


def _verificar_permisos_transportes(usuario: Usuario):
    if usuario.rol not in ["super_admin", "admin_transportes"]:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos para consultar el historial de rutas"
        )


def formatear_fecha_espanol(fecha_str: str) -> str:
    """Convierte fecha de formato YYYY-MM-DD a dd/mm/YYYY"""
    try:
        fecha = datetime.fromisoformat(fecha_str).date()
        return f"{fecha.day:02d}/{fecha.month:02d}/{fecha.year}"
    except Exception:
        return fecha_str


def formatear_datetime_espanol(dt) -> Optional[str]:
    """Formatea datetime a dd/mm/YYYY HH:MM"""
    if dt is None:
        return None
    try:
        if hasattr(dt, "strftime"):
            return dt.strftime("%d/%m/%Y %H:%M")
        if isinstance(dt, str):
            parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            return parsed.strftime("%d/%m/%Y %H:%M")
    except Exception:
        pass
    return str(dt)


def estado_pedido_label(estado: Optional[str]) -> str:
    """Texto amigable del estado del pedido (igual que en la sección Pedidos)."""
    labels = {
        "pendiente": "Pendiente",
        "en_ruta": "En ruta",
        "entregado": "Entregado",
        "incidencia": "Incidencia",
        "cancelado": "Cancelado",
    }
    key = (estado or "").strip().lower()
    return labels.get(key, estado or "-")


def _build_pdf(titulo: str, subtitulo: str, headers: list, rows: list) -> bytes:
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    except ImportError:
        raise HTTPException(status_code=500, detail="reportlab no está instalado")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        leftMargin=20, rightMargin=20, topMargin=24, bottomMargin=24
    )
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(titulo, styles["Title"]))
    story.append(Paragraph(subtitulo, styles["Normal"]))
    story.append(Spacer(1, 12))
    data = [headers] + rows
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f2f4f7")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#2f343d")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e0e0e0")),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(table)
    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def get_first_and_last_day_of_month(year: int, month: int):
    from calendar import monthrange
    first_day = date(year, month, 1)
    last_day = date(year, month, monthrange(year, month)[1])
    return first_day, last_day


async def obtener_historial_pedidos(
    fecha_desde: Optional[str],
    fecha_hasta: Optional[str],
    solo_con_ruta: bool,
    db: Session,
    current_user: Usuario,
):
    _verificar_permisos_transportes(current_user)

    query = db.query(Pedido)

    # Por defecto: mes actual si no se especifican fechas
    if not fecha_desde and not fecha_hasta:
        today = date.today()
        fecha_desde = get_first_and_last_day_of_month(today.year, today.month)[0].isoformat()
        fecha_hasta = get_first_and_last_day_of_month(today.year, today.month)[1].isoformat()

    if fecha_desde:
        try:
            f_desde = datetime.fromisoformat(fecha_desde).date()
        except ValueError:
            f_desde = date.today()
        query = query.filter(Pedido.fecha_entrega_deseada >= f_desde)
    if fecha_hasta:
        try:
            f_hasta = datetime.fromisoformat(fecha_hasta).date()
        except ValueError:
            f_hasta = date.today()
        query = query.filter(Pedido.fecha_entrega_deseada <= f_hasta)

    # Obtener pedidos que cumplan filtro de fecha
    pedidos = query.order_by(Pedido.fecha_entrega_deseada.desc(), Pedido.creado_en.desc()).all()

    if solo_con_ruta:
        # Solo pedidos que tienen al menos una RutaParada (asignados a alguna ruta)
        pedidos_con_ruta_ids = {row[0] for row in db.query(RutaParada.pedido_id).distinct().all()}
        pedidos = [p for p in pedidos if p.id in pedidos_con_ruta_ids]

    resultado = []
    for pedido in pedidos:
        # Ruta asignada: primera RutaParada del pedido (cualquiera) para obtener ruta_id
        ruta_parada_cualquiera = (
            db.query(RutaParada)
            .filter(RutaParada.pedido_id == pedido.id)
            .first()
        )
        ruta_info = None
        if ruta_parada_cualquiera and ruta_parada_cualquiera.ruta_id:
            ruta = db.query(Ruta).filter(Ruta.id == ruta_parada_cualquiera.ruta_id).first()
            if ruta:
                conductor_nombre = None
                if ruta.conductor_id:
                    c = db.query(Conductor).filter(Conductor.id == ruta.conductor_id).first()
                    if c:
                        conductor_nombre = f"{c.nombre or ''} {c.apellidos or ''}".strip() or c.nombre
                vehiculo_matricula = None
                if ruta.vehiculo_id:
                    v = db.query(Vehiculo).filter(Vehiculo.id == ruta.vehiculo_id).first()
                    if v:
                        vehiculo_matricula = v.matricula
                ruta_info = {
                    "id": ruta.id,
                    "conductor": conductor_nombre,
                    "vehiculo": vehiculo_matricula,
                    "tooltip": f"Conductor: {conductor_nombre or '-'}\nVehículo: {vehiculo_matricula or '-'}",
                }

        # Fecha entregado: parada de DESCARGA del pedido marcada como ENTREGADO
        parada_descarga = (
            db.query(RutaParada)
            .filter(
                RutaParada.pedido_id == pedido.id,
                RutaParada.tipo_operacion == TipoOperacion.DESCARGA,
                RutaParada.estado == EstadoParada.ENTREGADO,
            )
            .first()
        )
        fecha_entregado = None
        if parada_descarga and parada_descarga.fecha_hora_completada:
            fecha_entregado = parada_descarga.fecha_hora_completada.isoformat() if hasattr(parada_descarga.fecha_hora_completada, "isoformat") else str(parada_descarga.fecha_hora_completada)

        estado_val = pedido.estado.value if hasattr(pedido.estado, "value") else str(pedido.estado)
        fecha_entrega_val = pedido.fecha_entrega_deseada.isoformat() if pedido.fecha_entrega_deseada else None

        resultado.append({
            "id": pedido.id,
            "empresa": pedido.cliente or "",
            "origen": pedido.origen or "",
            "destino": pedido.destino or "",
            "tipo_mercancia": pedido.tipo_mercancia or "",
            "fecha_entrega": fecha_entrega_val,
            "estado": estado_val,
            "ruta": ruta_info,
            "fecha_entregado": fecha_entregado,
        })

    return resultado


@router.get("/pedidos")
async def listar_historial_pedidos(
    fecha_desde: Optional[str] = Query(None, description="Fecha de entrega desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha de entrega hasta (YYYY-MM-DD)"),
    solo_con_ruta: bool = Query(False, description="Solo pedidos con ruta asignada"),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """
    Historial de pedidos con empresa, origen, destino, tipo mercancía, fecha entrega,
    estado, ruta (conductor/vehículo) y fecha en que se entregó (parada descarga completada).
    """
    return await obtener_historial_pedidos(fecha_desde, fecha_hasta, solo_con_ruta, db, current_user)


@router.get("/pedidos/exportar/{formato}")
async def exportar_historial_pedidos(
    formato: str,
    fecha_desde: Optional[str] = Query(None),
    fecha_hasta: Optional[str] = Query(None),
    solo_con_ruta: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    """Exporta historial de pedidos en CSV, Excel o PDF."""
    datos = await obtener_historial_pedidos(fecha_desde, fecha_hasta, solo_con_ruta, db, current_user)

    headers_display = [
        "Empresa", "Origen", "Destino", "Tipo mercancía", "Fecha entrega", "Estado",
        "Ruta (ID)", "Conductor", "Vehículo", "Fecha entregado"
    ]

    def row_for_export(item: dict) -> list:
        r = item.get("ruta") or {}
        return [
            item.get("empresa") or "",
            item.get("origen") or "",
            item.get("destino") or "",
            item.get("tipo_mercancia") or "",
            formatear_fecha_espanol(item["fecha_entrega"]) if item.get("fecha_entrega") else "",
            estado_pedido_label(item.get("estado")),
            str(r.get("id", "")),
            r.get("conductor") or "",
            r.get("vehiculo") or "",
            formatear_datetime_espanol(item.get("fecha_entregado")) or "",
        ]

    if formato.lower() == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Historial de rutas - Pedidos"])
        writer.writerow([])
        writer.writerow(headers_display)
        for item in datos:
            writer.writerow(row_for_export(item))
        csv_content = output.getvalue()
        output.close()
        filename = "historial_pedidos.csv"
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    if formato.lower() == "excel":
        try:
            import openpyxl
            from openpyxl.styles import Font, Alignment
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Historial Pedidos"
            ws.append(["Historial de rutas - Pedidos"])
            ws.append([])
            ws.append(headers_display)
            for item in datos:
                ws.append(row_for_export(item))
            for cell in ws[3]:
                cell.font = Font(bold=True)
                cell.alignment = Alignment(horizontal="center")
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            return Response(
                content=output.read(),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=historial_pedidos.xlsx"},
            )
        except ImportError:
            raise HTTPException(status_code=500, detail="openpyxl no está instalado")

    if formato.lower() == "pdf":
        titulo = "Historial de rutas - Pedidos"
        subtitulo = "Listado de pedidos con ruta, conductor y fecha de entrega"
        rows = [row_for_export(item) for item in datos]
        pdf_bytes = _build_pdf(titulo, subtitulo, headers_display, rows)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=historial_pedidos.pdf"},
        )

    raise HTTPException(status_code=400, detail="Formato no válido. Use: csv, excel o pdf")
