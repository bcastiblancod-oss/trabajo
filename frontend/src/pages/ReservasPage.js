import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getReservas, getDisponibilidad, getTiposHabitacion, getServiciosAdicionales, createReserva, cancelarReserva } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Calendar, Plus, X, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

const ReservasPage = () => {
  const { token, user, hasRole } = useAuth();
  const [reservas, setReservas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createModal, setCreateModal] = useState(false);
  const [cancelModal, setCancelModal] = useState(false);
  const [selectedReserva, setSelectedReserva] = useState(null);
  const [cancelMotivo, setCancelMotivo] = useState('');
  
  const [habitacionesDisponibles, setHabitacionesDisponibles] = useState([]);
  const [servicios, setServicios] = useState([]);
  const [formData, setFormData] = useState({
    habitacion_id: '',
    fecha_checkin: '',
    fecha_checkout: '',
    num_huespedes: 1,
    huesped: {
      nombre_completo: '',
      documento: '',
      email: '',
      telefono: '',
      ciudad: '',
      pais: 'Colombia'
    },
    servicios_adicionales: [],
    metodo_pago: 'tarjeta_credito',
    notas: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const data = await getReservas(token);
      setReservas(data);
      const serviciosData = await getServiciosAdicionales(token);
      setServicios(serviciosData);
    } catch (error) {
      toast.error('Error al cargar reservas');
    } finally {
      setLoading(false);
    }
  };

  const handleSearchRooms = async () => {
    if (!formData.fecha_checkin || !formData.fecha_checkout) {
      toast.error('Seleccione las fechas primero');
      return;
    }
    try {
      const data = await getDisponibilidad(token, {
        fecha_checkin: formData.fecha_checkin,
        fecha_checkout: formData.fecha_checkout,
        num_huespedes: formData.num_huespedes
      });
      setHabitacionesDisponibles(data.habitaciones_disponibles);
      if (data.total === 0) {
        toast.info('No hay habitaciones disponibles para las fechas seleccionadas');
      }
    } catch (error) {
      toast.error(error.message);
    }
  };

  const handleCreateReserva = async () => {
    try {
      const reservaData = {
        ...formData,
        servicios_adicionales: formData.servicios_adicionales
      };
      
      // If guest, prefill from user data
      if (hasRole('huesped')) {
        reservaData.huesped = {
          ...reservaData.huesped,
          nombre_completo: reservaData.huesped.nombre_completo || user.nombre_completo,
          documento: reservaData.huesped.documento || user.documento,
          email: reservaData.huesped.email || user.email,
          telefono: reservaData.huesped.telefono || user.telefono
        };
      }

      await createReserva(token, reservaData);
      toast.success('Reserva creada exitosamente');
      setCreateModal(false);
      resetForm();
      loadData();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const handleCancelReserva = async () => {
    try {
      const result = await cancelarReserva(token, selectedReserva.id, cancelMotivo);
      toast.success(result.mensaje);
      setCancelModal(false);
      setSelectedReserva(null);
      setCancelMotivo('');
      loadData();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const resetForm = () => {
    setFormData({
      habitacion_id: '',
      fecha_checkin: '',
      fecha_checkout: '',
      num_huespedes: 1,
      huesped: {
        nombre_completo: '',
        documento: '',
        email: '',
        telefono: '',
        ciudad: '',
        pais: 'Colombia'
      },
      servicios_adicionales: [],
      metodo_pago: 'tarjeta_credito',
      notas: ''
    });
    setHabitacionesDisponibles([]);
  };

  const getStatusBadge = (estado) => {
    const badges = {
      pendiente: 'bg-yellow-100 text-yellow-800',
      confirmada: 'bg-emerald-100 text-emerald-800',
      checked_in: 'bg-blue-100 text-blue-800',
      checked_out: 'bg-stone-100 text-stone-800',
      cancelada: 'bg-red-100 text-red-800',
      no_show: 'bg-orange-100 text-orange-800'
    };
    const labels = {
      pendiente: 'Pendiente',
      confirmada: 'Confirmada',
      checked_in: 'Check-in',
      checked_out: 'Check-out',
      cancelada: 'Cancelada',
      no_show: 'No Show'
    };
    return (
      <span className={`${badges[estado]} px-3 py-1 rounded-full text-xs font-medium`}>
        {labels[estado]}
      </span>
    );
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0
    }).format(value);
  };

  const canCancel = (reserva) => {
    return ['pendiente', 'confirmada'].includes(reserva.estado);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in" data-testid="reservas-page">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
        <div>
          <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-2">
            Gestión
          </p>
          <h1 className="text-3xl font-medium" style={{ fontFamily: 'Playfair Display, serif' }}>
            Reservas
          </h1>
        </div>
        <Button
          onClick={() => setCreateModal(true)}
          className="bg-primary text-primary-foreground h-12 px-6 rounded-sm"
          data-testid="create-reservation-btn"
        >
          <Plus className="w-4 h-4 mr-2" />
          Nueva Reserva
        </Button>
      </div>

      {/* Reservations Table */}
      <Card className="card-luxury">
        <CardContent className="p-0">
          {reservas.length === 0 ? (
            <div className="text-center py-16">
              <Calendar className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No hay reservas</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-stone-50/50">
                  <tr>
                    <th className="text-left py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Código</th>
                    <th className="text-left py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Huésped</th>
                    <th className="text-left py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Habitación</th>
                    <th className="text-left py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Fechas</th>
                    <th className="text-left py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Estado</th>
                    <th className="text-right py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Total</th>
                    <th className="text-right py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {reservas.map((reserva) => (
                    <tr key={reserva.id} className="border-b border-stone-100 last:border-0 hover:bg-stone-50/30 transition-colors" data-testid={`reservation-row-${reserva.codigo}`}>
                      <td className="py-4 px-6">
                        <span className="font-medium">{reserva.codigo}</span>
                      </td>
                      <td className="py-4 px-6">
                        <div>
                          <p className="font-medium">{reserva.huesped?.nombre_completo}</p>
                          <p className="text-sm text-muted-foreground">{reserva.huesped?.email}</p>
                        </div>
                      </td>
                      <td className="py-4 px-6">
                        <span className="font-medium">{reserva.habitacion?.numero}</span>
                        <span className="text-muted-foreground ml-1">({reserva.habitacion?.tipo_habitacion?.nombre})</span>
                      </td>
                      <td className="py-4 px-6">
                        <p className="text-sm">{reserva.fecha_checkin}</p>
                        <p className="text-sm text-muted-foreground">→ {reserva.fecha_checkout}</p>
                      </td>
                      <td className="py-4 px-6">{getStatusBadge(reserva.estado)}</td>
                      <td className="py-4 px-6 text-right font-medium">{formatCurrency(reserva.precio_total)}</td>
                      <td className="py-4 px-6 text-right">
                        {canCancel(reserva) && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => {
                              setSelectedReserva(reserva);
                              setCancelModal(true);
                            }}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            data-testid={`cancel-btn-${reserva.codigo}`}
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Modal */}
      <Dialog open={createModal} onOpenChange={(open) => { setCreateModal(open); if (!open) resetForm(); }}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Playfair Display, serif' }}>
              Nueva Reserva
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6 py-4">
            {/* Step 1: Dates */}
            <div className="p-4 bg-stone-50 rounded-sm">
              <h3 className="font-medium mb-4">1. Seleccione fechas y busque disponibilidad</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <Label>Check-in</Label>
                  <Input
                    type="date"
                    value={formData.fecha_checkin}
                    onChange={(e) => setFormData({...formData, fecha_checkin: e.target.value})}
                    className="mt-1"
                    data-testid="new-reservation-checkin"
                  />
                </div>
                <div>
                  <Label>Check-out</Label>
                  <Input
                    type="date"
                    value={formData.fecha_checkout}
                    onChange={(e) => setFormData({...formData, fecha_checkout: e.target.value})}
                    className="mt-1"
                    data-testid="new-reservation-checkout"
                  />
                </div>
                <div>
                  <Label>Huéspedes</Label>
                  <Input
                    type="number"
                    min="1"
                    value={formData.num_huespedes}
                    onChange={(e) => setFormData({...formData, num_huespedes: parseInt(e.target.value)})}
                    className="mt-1"
                    data-testid="new-reservation-guests"
                  />
                </div>
                <div className="flex items-end">
                  <Button onClick={handleSearchRooms} className="w-full" data-testid="search-rooms-btn">
                    Buscar
                  </Button>
                </div>
              </div>
            </div>

            {/* Step 2: Room Selection */}
            {habitacionesDisponibles.length > 0 && (
              <div className="p-4 bg-stone-50 rounded-sm">
                <h3 className="font-medium mb-4">2. Seleccione habitación</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-48 overflow-y-auto">
                  {habitacionesDisponibles.map((hab) => (
                    <div
                      key={hab.id}
                      onClick={() => setFormData({...formData, habitacion_id: hab.id})}
                      className={`p-3 border rounded-sm cursor-pointer transition-all ${
                        formData.habitacion_id === hab.id
                          ? 'border-primary bg-primary/5'
                          : 'border-stone-200 hover:border-stone-300'
                      }`}
                      data-testid={`select-room-${hab.numero}`}
                    >
                      <div className="flex justify-between">
                        <span className="font-medium">{hab.numero}</span>
                        <span className="text-sm text-muted-foreground">{hab.tipo_habitacion?.nombre}</span>
                      </div>
                      <p className="text-sm font-medium mt-1">{formatCurrency(hab.tipo_habitacion?.precio_base)}/noche</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Step 3: Guest Info */}
            {formData.habitacion_id && (
              <div className="p-4 bg-stone-50 rounded-sm">
                <h3 className="font-medium mb-4">3. Datos del huésped</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>Nombre completo *</Label>
                    <Input
                      value={formData.huesped.nombre_completo}
                      onChange={(e) => setFormData({...formData, huesped: {...formData.huesped, nombre_completo: e.target.value}})}
                      className="mt-1"
                      data-testid="guest-name-input"
                    />
                  </div>
                  <div>
                    <Label>Documento *</Label>
                    <Input
                      value={formData.huesped.documento}
                      onChange={(e) => setFormData({...formData, huesped: {...formData.huesped, documento: e.target.value}})}
                      className="mt-1"
                      data-testid="guest-document-input"
                    />
                  </div>
                  <div>
                    <Label>Email *</Label>
                    <Input
                      type="email"
                      value={formData.huesped.email}
                      onChange={(e) => setFormData({...formData, huesped: {...formData.huesped, email: e.target.value}})}
                      className="mt-1"
                      data-testid="guest-email-input"
                    />
                  </div>
                  <div>
                    <Label>Teléfono *</Label>
                    <Input
                      value={formData.huesped.telefono}
                      onChange={(e) => setFormData({...formData, huesped: {...formData.huesped, telefono: e.target.value}})}
                      className="mt-1"
                      data-testid="guest-phone-input"
                    />
                  </div>
                  <div>
                    <Label>Ciudad</Label>
                    <Input
                      value={formData.huesped.ciudad}
                      onChange={(e) => setFormData({...formData, huesped: {...formData.huesped, ciudad: e.target.value}})}
                      className="mt-1"
                    />
                  </div>
                  <div>
                    <Label>Método de pago</Label>
                    <Select value={formData.metodo_pago} onValueChange={(v) => setFormData({...formData, metodo_pago: v})}>
                      <SelectTrigger className="mt-1">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="tarjeta_credito">Tarjeta de crédito</SelectItem>
                        <SelectItem value="tarjeta_debito">Tarjeta débito</SelectItem>
                        <SelectItem value="efectivo">Efectivo</SelectItem>
                        <SelectItem value="transferencia">Transferencia</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="mt-4">
                  <Label>Notas</Label>
                  <Textarea
                    value={formData.notas}
                    onChange={(e) => setFormData({...formData, notas: e.target.value})}
                    className="mt-1"
                    placeholder="Solicitudes especiales, hora de llegada, etc."
                  />
                </div>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => { setCreateModal(false); resetForm(); }}>
              Cancelar
            </Button>
            <Button 
              onClick={handleCreateReserva}
              disabled={!formData.habitacion_id || !formData.huesped.nombre_completo || !formData.huesped.documento || !formData.huesped.email || !formData.huesped.telefono}
              data-testid="confirm-reservation-btn"
            >
              Crear Reserva
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Cancel Modal */}
      <Dialog open={cancelModal} onOpenChange={setCancelModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              Cancelar Reserva
            </DialogTitle>
            <DialogDescription>
              Esta acción cancelará la reserva {selectedReserva?.codigo}. 
              Se aplicará la política de reembolso según el tiempo de anticipación.
            </DialogDescription>
          </DialogHeader>
          <div className="py-4">
            <Label>Motivo de cancelación</Label>
            <Textarea
              value={cancelMotivo}
              onChange={(e) => setCancelMotivo(e.target.value)}
              className="mt-2"
              placeholder="Opcional: indique el motivo de la cancelación"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCancelModal(false)}>
              Volver
            </Button>
            <Button variant="destructive" onClick={handleCancelReserva} data-testid="confirm-cancel-btn">
              Confirmar Cancelación
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ReservasPage;
