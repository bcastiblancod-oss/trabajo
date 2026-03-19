import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getDashboard, getReservas } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { 
  BedDouble, Users, Calendar, DollarSign, 
  TrendingUp, ArrowUpRight, ArrowDownRight, Clock
} from 'lucide-react';
import { toast } from 'sonner';

const DashboardPage = () => {
  const { token, user, hasRole } = useAuth();
  const [dashboard, setDashboard] = useState(null);
  const [reservas, setReservas] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      if (hasRole('administrador', 'recepcionista')) {
        const data = await getDashboard(token);
        setDashboard(data);
      }
      const reservasData = await getReservas(token, { limit: 5 });
      setReservas(reservasData);
    } catch (error) {
      toast.error('Error al cargar el dashboard');
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

  const getStatusBadge = (estado) => {
    const badges = {
      disponible: 'badge-disponible',
      reservada: 'badge-reservada',
      ocupada: 'badge-ocupada',
      confirmada: 'badge-confirmada',
      cancelada: 'badge-cancelada',
      checked_in: 'badge-checked_in',
      checked_out: 'badge-checked_out',
      pendiente: 'bg-yellow-100 text-yellow-800 px-3 py-1 rounded-full text-xs font-medium'
    };
    const labels = {
      disponible: 'Disponible',
      reservada: 'Reservada',
      ocupada: 'Ocupada',
      confirmada: 'Confirmada',
      cancelada: 'Cancelada',
      checked_in: 'Check-in',
      checked_out: 'Check-out',
      pendiente: 'Pendiente'
    };
    return <span className={badges[estado] || badges.pendiente}>{labels[estado] || estado}</span>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  // Guest dashboard
  if (hasRole('huesped')) {
    return (
      <div className="animate-fade-in" data-testid="guest-dashboard">
        <div className="mb-8">
          <h1 className="text-3xl font-medium" style={{ fontFamily: 'Playfair Display, serif' }}>
            Bienvenido, {user?.nombre_completo}
          </h1>
          <p className="text-muted-foreground mt-2">
            Gestione sus reservas en Hotel Imperium
          </p>
        </div>

        <Card className="card-luxury mb-8">
          <CardHeader>
            <CardTitle className="text-lg">Mis Reservas</CardTitle>
          </CardHeader>
          <CardContent>
            {reservas.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">
                No tiene reservas activas
              </p>
            ) : (
              <div className="space-y-4">
                {reservas.map((reserva) => (
                  <div 
                    key={reserva.id} 
                    className="flex items-center justify-between p-4 bg-stone-50 rounded-sm"
                  >
                    <div>
                      <p className="font-medium">{reserva.codigo}</p>
                      <p className="text-sm text-muted-foreground">
                        {reserva.fecha_checkin} - {reserva.fecha_checkout}
                      </p>
                    </div>
                    <div className="text-right">
                      {getStatusBadge(reserva.estado)}
                      <p className="text-sm font-medium mt-1">{formatCurrency(reserva.precio_total)}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  }

  // Staff dashboard
  return (
    <div className="animate-fade-in" data-testid="staff-dashboard">
      <div className="mb-8">
        <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-2">
          Dashboard
        </p>
        <h1 className="text-3xl font-medium" style={{ fontFamily: 'Playfair Display, serif' }}>
          Bienvenido, {user?.nombre_completo}
        </h1>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {/* Ocupación */}
        <Card className="card-luxury">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-2">
                  Ocupación
                </p>
                <p className="stat-number text-primary">
                  {dashboard?.habitaciones?.tasa_ocupacion || 0}%
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  {dashboard?.habitaciones?.ocupadas || 0} de {dashboard?.habitaciones?.total || 24} habitaciones
                </p>
              </div>
              <div className="w-12 h-12 bg-primary/10 rounded-sm flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-primary" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Disponibles */}
        <Card className="card-luxury">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-2">
                  Disponibles
                </p>
                <p className="stat-number text-emerald-600">
                  {dashboard?.habitaciones?.disponibles || 0}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  Listas para reservar
                </p>
              </div>
              <div className="w-12 h-12 bg-emerald-50 rounded-sm flex items-center justify-center">
                <BedDouble className="w-6 h-6 text-emerald-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Check-ins Hoy */}
        <Card className="card-luxury">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-2">
                  Check-ins Hoy
                </p>
                <p className="stat-number text-blue-600">
                  {dashboard?.movimientos_hoy?.checkins_pendientes || 0}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  Pendientes de llegada
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-50 rounded-sm flex items-center justify-center">
                <ArrowDownRight className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Check-outs Hoy */}
        <Card className="card-luxury">
          <CardContent className="pt-6">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-2">
                  Check-outs Hoy
                </p>
                <p className="stat-number text-amber-600">
                  {dashboard?.movimientos_hoy?.checkouts_pendientes || 0}
                </p>
                <p className="text-sm text-muted-foreground mt-1">
                  Salidas programadas
                </p>
              </div>
              <div className="w-12 h-12 bg-amber-50 rounded-sm flex items-center justify-center">
                <ArrowUpRight className="w-6 h-6 text-amber-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Second Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Ingresos */}
        <Card className="card-luxury lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <DollarSign className="w-5 h-5 text-amber-600" />
              Ingresos
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-8">
              <div>
                <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-2">
                  Hoy
                </p>
                <p className="text-3xl font-semibold" style={{ fontFamily: 'Playfair Display, serif' }}>
                  {formatCurrency(dashboard?.ingresos?.hoy || 0)}
                </p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-2">
                  Este Mes
                </p>
                <p className="text-3xl font-semibold" style={{ fontFamily: 'Playfair Display, serif' }}>
                  {formatCurrency(dashboard?.ingresos?.mes || 0)}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Estado Habitaciones */}
        <Card className="card-luxury">
          <CardHeader>
            <CardTitle className="text-lg">Estado Habitaciones</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">Ocupadas</span>
                <span className="badge-ocupada">{dashboard?.habitaciones?.ocupadas || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Disponibles</span>
                <span className="badge-disponible">{dashboard?.habitaciones?.disponibles || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Mantenimiento</span>
                <span className="badge-mantenimiento">{dashboard?.habitaciones?.mantenimiento || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Limpieza</span>
                <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-xs font-medium">
                  {dashboard?.habitaciones?.limpieza || 0}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Reservations */}
      <Card className="card-luxury">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            Reservas Recientes
          </CardTitle>
        </CardHeader>
        <CardContent>
          {reservas.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">
              No hay reservas recientes
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full table-luxury">
                <thead>
                  <tr>
                    <th className="text-left py-3 px-4">Código</th>
                    <th className="text-left py-3 px-4">Huésped</th>
                    <th className="text-left py-3 px-4">Habitación</th>
                    <th className="text-left py-3 px-4">Fechas</th>
                    <th className="text-left py-3 px-4">Estado</th>
                    <th className="text-right py-3 px-4">Total</th>
                  </tr>
                </thead>
                <tbody>
                  {reservas.map((reserva) => (
                    <tr key={reserva.id} className="border-b border-stone-100 last:border-0">
                      <td className="py-4 px-4 font-medium">{reserva.codigo}</td>
                      <td className="py-4 px-4">{reserva.huesped?.nombre_completo}</td>
                      <td className="py-4 px-4">{reserva.habitacion?.numero}</td>
                      <td className="py-4 px-4 text-sm text-muted-foreground">
                        {reserva.fecha_checkin} → {reserva.fecha_checkout}
                      </td>
                      <td className="py-4 px-4">{getStatusBadge(reserva.estado)}</td>
                      <td className="py-4 px-4 text-right font-medium">
                        {formatCurrency(reserva.precio_total)}
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

export default DashboardPage;
