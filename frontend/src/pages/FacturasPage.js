import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getFacturas } from '../services/api';
import { Card, CardContent } from '../components/ui/card';
import { FileText, Download } from 'lucide-react';
import { toast } from 'sonner';

const FacturasPage = () => {
  const { token } = useAuth();
  const [facturas, setFacturas] = useState([]);
  const [loading, setLoading] = useState(true);

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
