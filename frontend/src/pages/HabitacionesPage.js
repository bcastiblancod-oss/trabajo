import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getHabitaciones, getTiposHabitacion, getDisponibilidad, updateHabitacion } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { BedDouble, Users, Wifi, Tv, Wind, Search, Filter } from 'lucide-react';
import { toast } from 'sonner';

const HabitacionesPage = () => {
  const { token, hasRole } = useAuth();
  const [habitaciones, setHabitaciones] = useState([]);
  const [tipos, setTipos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    piso: '',
    tipo_habitacion_id: '',
    estado: ''
  });
  const [disponibilidadModal, setDisponibilidadModal] = useState(false);
  const [disponibilidadFilters, setDisponibilidadFilters] = useState({
    fecha_checkin: '',
    fecha_checkout: '',
    num_huespedes: ''
  });
  const [disponibles, setDisponibles] = useState(null);
  const [editModal, setEditModal] = useState(false);
  const [selectedRoom, setSelectedRoom] = useState(null);
  const [editData, setEditData] = useState({ estado: '' });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [habData, tiposData] = await Promise.all([
        getHabitaciones(token),
        getTiposHabitacion(token)
      ]);
      setHabitaciones(habData);
      setTipos(tiposData);
    } catch (error) {
      toast.error('Error al cargar habitaciones');
    } finally {
      setLoading(false);
    }
  };

  const handleFilter = async () => {
    setLoading(true);
    try {
      const params = {};
      if (filters.piso) params.piso = filters.piso;
      if (filters.tipo_habitacion_id) params.tipo_habitacion_id = filters.tipo_habitacion_id;
      if (filters.estado) params.estado = filters.estado;
      const data = await getHabitaciones(token, params);
      setHabitaciones(data);
    } catch (error) {
      toast.error('Error al filtrar');
    } finally {
      setLoading(false);
    }
  };

  const handleDisponibilidad = async () => {
    if (!disponibilidadFilters.fecha_checkin || !disponibilidadFilters.fecha_checkout) {
      toast.error('Seleccione las fechas');
      return;
    }
    try {
      const data = await getDisponibilidad(token, disponibilidadFilters);
      setDisponibles(data);
    } catch (error) {
      toast.error(error.message);
    }
  };

  const handleEditRoom = (room) => {
    setSelectedRoom(room);
    setEditData({ estado: room.estado });
    setEditModal(true);
  };

  const handleUpdateRoom = async () => {
    try {
      await updateHabitacion(token, selectedRoom.id, editData);
      toast.success('Habitación actualizada');
      setEditModal(false);
      loadData();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const getStatusBadge = (estado) => {
    const badges = {
      disponible: 'badge-disponible',
      reservada: 'badge-reservada',
      ocupada: 'badge-ocupada',
      mantenimiento: 'badge-mantenimiento',
      fuera_de_servicio: 'bg-red-100 text-red-800 px-3 py-1 rounded-full text-xs font-medium',
      para_limpieza: 'bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-xs font-medium'
    };
    const labels = {
      disponible: 'Disponible',
      reservada: 'Reservada',
      ocupada: 'Ocupada',
      mantenimiento: 'Mantenimiento',
      fuera_de_servicio: 'Fuera de servicio',
      para_limpieza: 'Para limpieza'
    };
    return <span className={badges[estado]}>{labels[estado]}</span>;
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0
    }).format(value);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in" data-testid="habitaciones-page">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
        <div>
          <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-2">
            Gestión
          </p>
          <h1 className="text-3xl font-medium" style={{ fontFamily: 'Playfair Display, serif' }}>
            Habitaciones
          </h1>
        </div>
        <Button
          onClick={() => setDisponibilidadModal(true)}
          className="bg-primary text-primary-foreground h-12 px-6 rounded-sm"
          data-testid="check-availability-btn"
        >
          <Search className="w-4 h-4 mr-2" />
          Consultar Disponibilidad
        </Button>
      </div>

      {/* Filters */}
      <Card className="card-luxury mb-8">
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Label className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
                Piso
              </Label>
              <Select value={filters.piso || "all"} onValueChange={(v) => setFilters({...filters, piso: v === "all" ? "" : v})}>
                <SelectTrigger className="mt-2" data-testid="filter-floor">
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  <SelectItem value="1">Piso 1</SelectItem>
                  <SelectItem value="2">Piso 2</SelectItem>
                  <SelectItem value="3">Piso 3</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
                Tipo
              </Label>
              <Select value={filters.tipo_habitacion_id || "all"} onValueChange={(v) => setFilters({...filters, tipo_habitacion_id: v === "all" ? "" : v})}>
                <SelectTrigger className="mt-2" data-testid="filter-type">
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  {tipos.map((tipo) => (
                    <SelectItem key={tipo.id} value={tipo.id}>{tipo.nombre}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
                Estado
              </Label>
              <Select value={filters.estado || "all"} onValueChange={(v) => setFilters({...filters, estado: v === "all" ? "" : v})}>
                <SelectTrigger className="mt-2" data-testid="filter-status">
                  <SelectValue placeholder="Todos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos</SelectItem>
                  <SelectItem value="disponible">Disponible</SelectItem>
                  <SelectItem value="reservada">Reservada</SelectItem>
                  <SelectItem value="ocupada">Ocupada</SelectItem>
                  <SelectItem value="mantenimiento">Mantenimiento</SelectItem>
                  <SelectItem value="para_limpieza">Para limpieza</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-end">
              <Button onClick={handleFilter} variant="outline" className="w-full h-10" data-testid="apply-filters-btn">
                <Filter className="w-4 h-4 mr-2" />
                Filtrar
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Rooms Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {habitaciones.map((hab) => (
          <Card 
            key={hab.id} 
            className="card-luxury group cursor-pointer hover:shadow-lg transition-all duration-300"
            onClick={() => hasRole('administrador', 'recepcionista') && handleEditRoom(hab)}
            data-testid={`room-card-${hab.numero}`}
          >
            <CardContent className="pt-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-2xl font-semibold" style={{ fontFamily: 'Playfair Display, serif' }}>
                    {hab.numero}
                  </p>
                  <p className="text-sm text-muted-foreground">Piso {hab.piso}</p>
                </div>
                {getStatusBadge(hab.estado)}
              </div>
              
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <BedDouble className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm font-medium">{hab.tipo_habitacion?.nombre}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Users className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">Hasta {hab.tipo_habitacion?.capacidad_maxima} huéspedes</span>
                </div>
                <div className="flex items-center gap-4 text-muted-foreground">
                  <Wifi className="w-4 h-4" />
                  <Tv className="w-4 h-4" />
                  <Wind className="w-4 h-4" />
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-stone-100">
                <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
                  Precio base / noche
                </p>
                <p className="text-xl font-semibold mt-1" style={{ fontFamily: 'Playfair Display, serif' }}>
                  {formatCurrency(hab.tipo_habitacion?.precio_base || 0)}
                </p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Disponibilidad Modal */}
      <Dialog open={disponibilidadModal} onOpenChange={setDisponibilidadModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Playfair Display, serif' }}>
              Consultar Disponibilidad
            </DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 py-4">
            <div>
              <Label className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
                Check-in
              </Label>
              <Input
                type="date"
                value={disponibilidadFilters.fecha_checkin}
                onChange={(e) => setDisponibilidadFilters({...disponibilidadFilters, fecha_checkin: e.target.value})}
                className="mt-2"
                data-testid="availability-checkin"
              />
            </div>
            <div>
              <Label className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
                Check-out
              </Label>
              <Input
                type="date"
                value={disponibilidadFilters.fecha_checkout}
                onChange={(e) => setDisponibilidadFilters({...disponibilidadFilters, fecha_checkout: e.target.value})}
                className="mt-2"
                data-testid="availability-checkout"
              />
            </div>
            <div>
              <Label className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
                Huéspedes
              </Label>
              <Input
                type="number"
                min="1"
                value={disponibilidadFilters.num_huespedes}
                onChange={(e) => setDisponibilidadFilters({...disponibilidadFilters, num_huespedes: e.target.value})}
                className="mt-2"
                data-testid="availability-guests"
              />
            </div>
          </div>
          <Button onClick={handleDisponibilidad} className="w-full" data-testid="search-availability-btn">
            Buscar
          </Button>

          {disponibles && (
            <div className="mt-4 border-t pt-4">
              <p className="text-sm font-medium mb-4">
                {disponibles.total} habitaciones disponibles
              </p>
              <div className="max-h-64 overflow-y-auto space-y-2">
                {disponibles.habitaciones_disponibles.map((hab) => (
                  <div key={hab.id} className="flex items-center justify-between p-3 bg-stone-50 rounded-sm">
                    <div>
                      <span className="font-medium">{hab.numero}</span>
                      <span className="text-muted-foreground ml-2">- {hab.tipo_habitacion?.nombre}</span>
                    </div>
                    <span className="font-medium">{formatCurrency(hab.tipo_habitacion?.precio_base)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Edit Modal */}
      <Dialog open={editModal} onOpenChange={setEditModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Playfair Display, serif' }}>
              Editar Habitación {selectedRoom?.numero}
            </DialogTitle>
          </DialogHeader>
          <div className="py-4">
            <Label className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
              Estado
            </Label>
            <Select value={editData.estado || "disponible"} onValueChange={(v) => setEditData({...editData, estado: v})}>
              <SelectTrigger className="mt-2" data-testid="edit-room-status">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="disponible">Disponible</SelectItem>
                <SelectItem value="mantenimiento">Mantenimiento</SelectItem>
                <SelectItem value="fuera_de_servicio">Fuera de servicio</SelectItem>
                <SelectItem value="para_limpieza">Para limpieza</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditModal(false)}>Cancelar</Button>
            <Button onClick={handleUpdateRoom} data-testid="save-room-btn">Guardar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default HabitacionesPage;
