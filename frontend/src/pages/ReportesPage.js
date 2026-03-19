import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getReporteOcupacion, getTopClientes } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { BarChart3, TrendingUp, Users, DollarSign } from 'lucide-react';
import { toast } from 'sonner';

const ReportesPage = () => {
  const { token } = useAuth();
  const [loading, setLoading] = useState(false);
  const [fechaInicio, setFechaInicio] = useState('');
  const [fechaFin, setFechaFin] = useState('');
  const [ocupacion, setOcupacion] = useState(null);
  const [topClientes, setTopClientes] = useState([]);

  useEffect(() => {
    // Set default dates (last 30 days)
    const end = new Date();
    const start = new Date();
    start.setDate(start.getDate() - 30);
    setFechaInicio(start.toISOString().split('T')[0]);
    setFechaFin(end.toISOString().split('T')[0]);
  }, []);

  const loadReportes = async () => {
    if (!fechaInicio || !fechaFin) {
      toast.error('Seleccione el rango de fechas');
      return;
    }
    
    setLoading(true);
    try {
      const [ocupacionData, clientesData] = await Promise.all([
        getReporteOcupacion(token, fechaInicio, fechaFin),
        getTopClientes(token, 10)
      ]);
      setOcupacion(ocupacionData);
      setTopClientes(clientesData);
    } catch (error) {
      toast.error(error.message);
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

  return (
    <div className="animate-fade-in" data-testid="reportes-page">
      <div className="mb-8">
        <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-2">
          Administración
        </p>
        <h1 className="text-3xl font-medium" style={{ fontFamily: 'Playfair Display, serif' }}>
          Reportes
        </h1>
      </div>

      {/* Date Filter */}
      <Card className="card-luxury mb-8">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4 items-end">
            <div className="flex-1">
              <Label className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
                Fecha inicio
              </Label>
              <Input
                type="date"
                value={fechaInicio}
                onChange={(e) => setFechaInicio(e.target.value)}
                className="mt-2"
                data-testid="report-date-start"
              />
            </div>
            <div className="flex-1">
              <Label className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
                Fecha fin
              </Label>
              <Input
                type="date"
                value={fechaFin}
                onChange={(e) => setFechaFin(e.target.value)}
                className="mt-2"
                data-testid="report-date-end"
              />
            </div>
            <Button onClick={loadReportes} disabled={loading} className="h-10" data-testid="generate-report-btn">
              {loading ? 'Cargando...' : 'Generar Reporte'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {ocupacion && (
        <>
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            <Card className="card-luxury">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-2">
                      Tasa de Ocupación
                    </p>
                    <p className="text-4xl font-semibold" style={{ fontFamily: 'Playfair Display, serif' }}>
                      {ocupacion.tasa_ocupacion}%
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-primary/10 rounded-sm flex items-center justify-center">
                    <TrendingUp className="w-6 h-6 text-primary" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="card-luxury">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-2">
                      Ingresos Totales
                    </p>
                    <p className="text-3xl font-semibold" style={{ fontFamily: 'Playfair Display, serif' }}>
                      {formatCurrency(ocupacion.ingresos_totales)}
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-emerald-50 rounded-sm flex items-center justify-center">
                    <DollarSign className="w-6 h-6 text-emerald-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="card-luxury">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-2">
                      Reservas
                    </p>
                    <p className="text-4xl font-semibold" style={{ fontFamily: 'Playfair Display, serif' }}>
                      {ocupacion.reservas_realizadas}
                    </p>
                    <p className="text-sm text-red-500 mt-1">
                      {ocupacion.reservas_canceladas} canceladas
                    </p>
                  </div>
                  <div className="w-12 h-12 bg-blue-50 rounded-sm flex items-center justify-center">
                    <BarChart3 className="w-6 h-6 text-blue-600" />
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="card-luxury">
              <CardContent className="pt-6">
                <div className="flex items-start justify-between">
                  <div>
                    <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-2">
                      Promedio Estancia
                    </p>
                    <p className="text-4xl font-semibold" style={{ fontFamily: 'Playfair Display, serif' }}>
                      {ocupacion.promedio_estancia}
                    </p>
                    <p className="text-sm text-muted-foreground mt-1">noches</p>
                  </div>
                  <div className="w-12 h-12 bg-amber-50 rounded-sm flex items-center justify-center">
                    <Users className="w-6 h-6 text-amber-600" />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Top Clientes */}
          <Card className="card-luxury">
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Users className="w-5 h-5" />
                Top 10 Clientes
              </CardTitle>
            </CardHeader>
            <CardContent>
              {topClientes.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">
                  No hay datos de clientes
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-stone-50/50">
                      <tr>
                        <th className="text-left py-3 px-4 text-xs uppercase tracking-widest font-semibold text-muted-foreground">#</th>
                        <th className="text-left py-3 px-4 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Cliente</th>
                        <th className="text-left py-3 px-4 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Documento</th>
                        <th className="text-center py-3 px-4 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Reservas</th>
                        <th className="text-right py-3 px-4 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Total Gastado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {topClientes.map((cliente, index) => (
                        <tr key={cliente.documento} className="border-b border-stone-100 last:border-0">
                          <td className="py-4 px-4">
                            <span className={`w-6 h-6 rounded-full inline-flex items-center justify-center text-xs font-semibold ${
                              index === 0 ? 'bg-amber-100 text-amber-800' :
                              index === 1 ? 'bg-stone-200 text-stone-800' :
                              index === 2 ? 'bg-orange-100 text-orange-800' :
                              'bg-stone-100 text-stone-600'
                            }`}>
                              {index + 1}
                            </span>
                          </td>
                          <td className="py-4 px-4">
                            <p className="font-medium">{cliente.nombre}</p>
                            <p className="text-sm text-muted-foreground">{cliente.email}</p>
                          </td>
                          <td className="py-4 px-4 text-sm">{cliente.documento}</td>
                          <td className="py-4 px-4 text-center">
                            <span className="bg-primary/10 text-primary px-2 py-1 rounded-full text-sm font-medium">
                              {cliente.total_reservas}
                            </span>
                          </td>
                          <td className="py-4 px-4 text-right font-semibold">
                            {formatCurrency(cliente.total_gastado)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}

      {!ocupacion && !loading && (
        <Card className="card-luxury">
          <CardContent className="py-16 text-center">
            <BarChart3 className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              Seleccione un rango de fechas y genere el reporte
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ReportesPage;
