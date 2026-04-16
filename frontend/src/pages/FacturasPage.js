import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getFacturas, getFactura } from '../services/api';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { FileText, Download, Eye, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';

const FacturasPage = () => {
  const { token } = useAuth();
  const [facturas, setFacturas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [downloadingId, setDownloadingId] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const data = await getFacturas(token);
      setFacturas(data);
    } catch (error) {
      toast.error('Error al cargar facturas');
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0
    }).format(value);
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('es-CO', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatDateLong = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('es-CO', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getEstadoBadge = (estado) => {
    const badges = {
      emitida: 'bg-blue-100 text-blue-800',
      pagada: 'bg-emerald-100 text-emerald-800',
      anulada: 'bg-red-100 text-red-800'
    };
    return (
      <span className={`${badges[estado]} px-3 py-1 rounded-full text-xs font-medium capitalize`}>
        {estado}
      </span>
    );
  };

  const generatePDF = async (factura) => {
    setDownloadingId(factura.id);
    
    try {
      // Obtener detalles completos de la factura
      let facturaCompleta = factura;
      try {
        facturaCompleta = await getFactura(token, factura.id);
      } catch (e) {
        // Si falla, usar los datos que ya tenemos
      }

      const doc = new jsPDF();
      const pageWidth = doc.internal.pageSize.getWidth();
      
      // Colores del tema
      const primaryColor = [30, 58, 52]; // Verde oscuro del hotel
      const accentColor = [16, 185, 129]; // Verde esmeralda
      
      // Header con fondo
      doc.setFillColor(...primaryColor);
      doc.rect(0, 0, pageWidth, 45, 'F');
      
      // Logo/Nombre del Hotel
      doc.setTextColor(255, 255, 255);
      doc.setFontSize(24);
      doc.setFont('helvetica', 'bold');
      doc.text('Hotel Imperium', 20, 22);
      
      doc.setFontSize(10);
      doc.setFont('helvetica', 'normal');
      doc.text('BOUTIQUE HOTEL', 20, 30);
      doc.text('NIT: 900.123.456-7', 20, 37);
      
      // Número de factura en el header
      doc.setFontSize(12);
      doc.setFont('helvetica', 'bold');
      doc.text('FACTURA', pageWidth - 60, 22);
      doc.setFontSize(14);
      doc.text(facturaCompleta.numero || 'N/A', pageWidth - 60, 32);
      
      // Estado de la factura
      const estado = (facturaCompleta.estado || 'emitida').toUpperCase();
      doc.setFontSize(10);
      if (estado === 'PAGADA') {
        doc.setTextColor(...accentColor);
      } else if (estado === 'ANULADA') {
        doc.setTextColor(239, 68, 68);
      } else {
        doc.setTextColor(59, 130, 246);
      }
      doc.text(estado, pageWidth - 60, 40);
      
      // Información de la factura
      doc.setTextColor(60, 60, 60);
      doc.setFontSize(10);
      
      let yPos = 60;
      
      // Fecha de emisión
      doc.setFont('helvetica', 'bold');
      doc.text('Fecha de Emisión:', 20, yPos);
      doc.setFont('helvetica', 'normal');
      doc.text(formatDateLong(facturaCompleta.fecha_emision), 70, yPos);
      
      yPos += 15;
      
      // Sección Cliente
      doc.setFillColor(245, 245, 245);
      doc.rect(15, yPos - 5, pageWidth - 30, 35, 'F');
      
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(11);
      doc.setTextColor(...primaryColor);
      doc.text('DATOS DEL CLIENTE', 20, yPos + 5);
      
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(10);
      doc.setTextColor(60, 60, 60);
      
      const cliente = facturaCompleta.huesped || {};
      doc.text(`Nombre: ${cliente.nombre_completo || 'N/A'}`, 20, yPos + 15);
      doc.text(`Documento: ${cliente.documento || 'N/A'}`, 20, yPos + 23);
      doc.text(`Email: ${cliente.email || 'N/A'}`, pageWidth/2, yPos + 15);
      doc.text(`Teléfono: ${cliente.telefono || 'N/A'}`, pageWidth/2, yPos + 23);
      
      yPos += 45;
      
      // Información de la reserva
      if (facturaCompleta.reserva) {
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(11);
        doc.setTextColor(...primaryColor);
        doc.text('INFORMACIÓN DE LA RESERVA', 20, yPos);
        
        yPos += 10;
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(10);
        doc.setTextColor(60, 60, 60);
        
        const reserva = facturaCompleta.reserva;
        doc.text(`Código: ${reserva.codigo_reserva || 'N/A'}`, 20, yPos);
        doc.text(`Habitación: ${reserva.habitacion?.numero || 'N/A'} - ${reserva.habitacion?.tipo || ''}`, pageWidth/2, yPos);
        
        yPos += 8;
        doc.text(`Check-in: ${reserva.fecha_entrada ? formatDate(reserva.fecha_entrada) : 'N/A'}`, 20, yPos);
        doc.text(`Check-out: ${reserva.fecha_salida ? formatDate(reserva.fecha_salida) : 'N/A'}`, pageWidth/2, yPos);
        
        yPos += 15;
      }
      
      // Tabla de conceptos
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(11);
      doc.setTextColor(...primaryColor);
      doc.text('DETALLE DE FACTURACIÓN', 20, yPos);
      
      yPos += 5;
      
      // Crear tabla de items
      const items = [];
      
      // Item de hospedaje
      if (facturaCompleta.reserva) {
        const reserva = facturaCompleta.reserva;
        const noches = Math.ceil((new Date(reserva.fecha_salida) - new Date(reserva.fecha_entrada)) / (1000 * 60 * 60 * 24)) || 1;
        const precioNoche = facturaCompleta.subtotal ? facturaCompleta.subtotal / noches : (facturaCompleta.total / noches);
        
        items.push([
          `Hospedaje - Habitación ${reserva.habitacion?.numero || ''} (${reserva.habitacion?.tipo || 'Estándar'})`,
          noches.toString(),
          formatCurrency(precioNoche),
          formatCurrency(precioNoche * noches)
        ]);
      } else {
        items.push([
          'Servicios de Hospedaje',
          '1',
          formatCurrency(facturaCompleta.subtotal || facturaCompleta.total),
          formatCurrency(facturaCompleta.subtotal || facturaCompleta.total)
        ]);
      }
      
      // Consumos adicionales
      if (facturaCompleta.consumos && facturaCompleta.consumos.length > 0) {
        facturaCompleta.consumos.forEach(consumo => {
          items.push([
            consumo.descripcion || 'Consumo adicional',
            consumo.cantidad?.toString() || '1',
            formatCurrency(consumo.precio_unitario || 0),
            formatCurrency(consumo.total || 0)
          ]);
        });
      }
      
      autoTable(doc, {
        startY: yPos,
        head: [['Concepto', 'Cantidad', 'Precio Unit.', 'Total']],
        body: items,
        theme: 'striped',
        headStyles: {
          fillColor: primaryColor,
          textColor: [255, 255, 255],
          fontSize: 10,
          fontStyle: 'bold'
        },
        bodyStyles: {
          fontSize: 9,
          textColor: [60, 60, 60]
        },
        columnStyles: {
          0: { cellWidth: 90 },
          1: { cellWidth: 25, halign: 'center' },
          2: { cellWidth: 35, halign: 'right' },
          3: { cellWidth: 35, halign: 'right' }
        },
        margin: { left: 15, right: 15 },
        didDrawPage: (data) => {
          yPos = data.cursor.y + 15;
        }
      });
      
      // Ajustar yPos basado en el número de items
      yPos = yPos + (items.length * 10) + 30;
      
      // Totales
      const totalesX = pageWidth - 80;
      
      doc.setDrawColor(200, 200, 200);
      doc.line(totalesX - 10, yPos - 5, pageWidth - 15, yPos - 5);
      
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(10);
      doc.setTextColor(100, 100, 100);
      
      if (facturaCompleta.subtotal) {
        doc.text('Subtotal:', totalesX, yPos);
        doc.text(formatCurrency(facturaCompleta.subtotal), pageWidth - 20, yPos, { align: 'right' });
        yPos += 8;
      }
      
      if (facturaCompleta.impuestos) {
        doc.text('IVA (19%):', totalesX, yPos);
        doc.text(formatCurrency(facturaCompleta.impuestos), pageWidth - 20, yPos, { align: 'right' });
        yPos += 8;
      }
      
      // Total
      doc.setFillColor(...primaryColor);
      doc.rect(totalesX - 15, yPos - 3, pageWidth - totalesX + 5, 12, 'F');
      
      doc.setFont('helvetica', 'bold');
      doc.setFontSize(12);
      doc.setTextColor(255, 255, 255);
      doc.text('TOTAL:', totalesX, yPos + 5);
      doc.text(formatCurrency(facturaCompleta.total), pageWidth - 20, yPos + 5, { align: 'right' });
      
      // Footer
      const footerY = doc.internal.pageSize.getHeight() - 30;
      
      doc.setDrawColor(200, 200, 200);
      doc.line(15, footerY - 10, pageWidth - 15, footerY - 10);
      
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(8);
      doc.setTextColor(130, 130, 130);
      doc.text('Hotel Imperium - Calle Principal #123, Bogotá, Colombia', pageWidth / 2, footerY, { align: 'center' });
      doc.text('Tel: +57 300 123 4567 | Email: contacto@hotelimperium.com', pageWidth / 2, footerY + 5, { align: 'center' });
      doc.text('www.hotelimperium.com', pageWidth / 2, footerY + 10, { align: 'center' });
      
      // Guardar PDF
      const fileName = `Factura_${facturaCompleta.numero || facturaCompleta.id}_HotelImperium.pdf`;
      doc.save(fileName);
      
      toast.success('Factura descargada correctamente');
    } catch (error) {
      console.error('Error generating PDF:', error);
      toast.error('Error al generar el PDF');
    } finally {
      setDownloadingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in" data-testid="facturas-page">
      <div className="mb-8">
        <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-2">
          Gestión
        </p>
        <h1 className="text-3xl font-medium" style={{ fontFamily: 'Playfair Display, serif' }}>
          Facturas
        </h1>
      </div>

      <Card className="card-luxury">
        <CardContent className="p-0">
          {facturas.length === 0 ? (
            <div className="text-center py-16">
              <FileText className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No hay facturas</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-stone-50/50">
                  <tr>
                    <th className="text-left py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Número</th>
                    <th className="text-left py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Fecha</th>
                    <th className="text-left py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Cliente</th>
                    <th className="text-left py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Estado</th>
                    <th className="text-right py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Total</th>
                    <th className="text-center py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {facturas.map((factura) => (
                    <tr key={factura.id} className="border-b border-stone-100 last:border-0 hover:bg-stone-50/30 transition-colors">
                      <td className="py-4 px-6 font-medium">{factura.numero}</td>
                      <td className="py-4 px-6 text-sm text-muted-foreground">{formatDate(factura.fecha_emision)}</td>
                      <td className="py-4 px-6">
                        <div>
                          <p className="font-medium">{factura.huesped?.nombre_completo}</p>
                          <p className="text-sm text-muted-foreground">{factura.huesped?.documento}</p>
                        </div>
                      </td>
                      <td className="py-4 px-6">{getEstadoBadge(factura.estado)}</td>
                      <td className="py-4 px-6 text-right font-semibold">{formatCurrency(factura.total)}</td>
                      <td className="py-4 px-6">
                        <div className="flex items-center justify-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => generatePDF(factura)}
                            disabled={downloadingId === factura.id}
                            className="h-8 px-3 text-xs"
                            data-testid={`download-invoice-${factura.id}`}
                          >
                            {downloadingId === factura.id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <>
                                <Download className="w-4 h-4 mr-1" />
                                PDF
                              </>
                            )}
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default FacturasPage;
