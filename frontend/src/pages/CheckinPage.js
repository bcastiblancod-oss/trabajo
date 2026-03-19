import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { buscarReserva, processCheckin } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { UserCheck, Search, Calendar, BedDouble, Users, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';

const CheckinPage = () => {
  const { token } = useAuth();
  const [searchType, setSearchType] = useState('codigo');
  const [searchValue, setSearchValue] = useState('');
  const [reservas, setReservas] = useState([]);
  const [selectedReserva, setSelectedReserva] = useState(null);
  const [loading, setLoading] = useState(false);
  const [checkinResult, setCheckinResult] = useState(null);

  const handleSearch = async () => {
    if (!searchValue.trim()) {
      toast.error('Ingrese un valor de búsqueda');
      return;
    }
    
    setLoading(true);
    try {
      const params = {};
      if (searchType === 'codigo') params.codigo = searchValue;
      else if (searchType === 'documento') params.documento = searchValue;
      else if (searchType === 'nombre') params.nombre = searchValue;

      const data = await buscarReserva(token, params);
      setReservas(data);
      setSelectedReserva(null);
      setCheckinResult(null);
      
      if (data.length === 0) {
        toast.info('No se encontraron reservas');
      }
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCheckin = async () => {
    if (!selectedReserva) return;
    
    setLoading(true);
    try {
      const result = await processCheckin(token, { reserva_id: selectedReserva.id });
      setCheckinResult(result);
      toast.success('Check-in realizado exitosamente');
      setReservas([]);
      setSelectedReserva(null);
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
    <div className="animate-fade-in" data-testid="checkin-page">
      <div className="mb-8">
        <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-2">
          Recepción
        </p>
        <h1 className="text-3xl font-medium" style={{ fontFamily: 'Playfair Display, serif' }}>
          Check-in
        </h1>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Search Panel */}
        <Card className="card-luxury">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Search className="w-5 h-5" />
              Buscar Reserva
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <Label className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
                  Buscar por
                </Label>
                <div className="flex gap-2 mt-2">
                  {['codigo', 'documento', 'nombre'].map((type) => (
                    <Button
                      key={type}
                      variant={searchType === type ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setSearchType(type)}
                      data-testid={`search-type-${type}`}
                    >
                      {type === 'codigo' ? 'Código' : type === 'documento' ? 'Documento' : 'Nombre'}
                    </Button>
                  ))}
                </div>
              </div>

              <div>
                <Label className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
                  {searchType === 'codigo' ? 'Código de reserva' : searchType === 'documento' ? 'Documento del huésped' : 'Nombre del huésped'}
                </Label>
                <div className="flex gap-2 mt-2">
                  <Input
                    value={searchValue}
                    onChange={(e) => setSearchValue(e.target.value)}
                    placeholder={searchType === 'codigo' ? 'RES-XXXXXXXX-XXXX' : searchType === 'documento' ? '1234567890' : 'Juan Pérez'}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                    data-testid="checkin-search-input"
                  />
                  <Button onClick={handleSearch} disabled={loading} data-testid="checkin-search-btn">
                    {loading ? '...' : 'Buscar'}
                  </Button>
                </div>
              </div>

              {/* Search Results */}
              {reservas.length > 0 && (
                <div className="mt-6">
                  <Label className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-3 block">
                    Reservas encontradas
                  </Label>
                  <div className="space-y-2">
                    {reservas.map((reserva) => (
                      <div
                        key={reserva.id}
                        onClick={() => setSelectedReserva(reserva)}
                        className={`p-4 border rounded-sm cursor-pointer transition-all ${
                          selectedReserva?.id === reserva.id
                            ? 'border-primary bg-primary/5'
                            : 'border-stone-200 hover:border-stone-300'
                        }`}
                        data-testid={`reserva-result-${reserva.codigo}`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{reserva.codigo}</span>
                          <span className="text-sm bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full">
                            {reserva.estado}
                          </span>
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">
                          {reserva.huesped?.nombre_completo}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {reserva.fecha_checkin} → {reserva.fecha_checkout}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Details & Action Panel */}
        <div className="space-y-6">
          {selectedReserva && (
            <Card className="card-luxury">
              <CardHeader>
                <CardTitle className="text-lg">Detalles de la Reserva</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center gap-3 p-4 bg-stone-50 rounded-sm">
                    <Calendar className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm text-muted-foreground">Fechas</p>
                      <p className="font-medium">
                        {selectedReserva.fecha_checkin} → {selectedReserva.fecha_checkout}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 p-4 bg-stone-50 rounded-sm">
                    <BedDouble className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm text-muted-foreground">Habitación</p>
                      <p className="font-medium">
                        {selectedReserva.habitacion?.numero} - {selectedReserva.habitacion?.tipo_habitacion?.nombre}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 p-4 bg-stone-50 rounded-sm">
                    <Users className="w-5 h-5 text-muted-foreground" />
                    <div>
                      <p className="text-sm text-muted-foreground">Huésped</p>
                      <p className="font-medium">{selectedReserva.huesped?.nombre_completo}</p>
                      <p className="text-sm text-muted-foreground">
                        Doc: {selectedReserva.huesped?.documento}
                      </p>
                    </div>
                  </div>

                  <div className="pt-4 border-t">
                    <div className="flex justify-between items-center">
                      <span className="text-muted-foreground">Total reserva</span>
                      <span className="text-xl font-semibold" style={{ fontFamily: 'Playfair Display, serif' }}>
                        {formatCurrency(selectedReserva.precio_total)}
                      </span>
                    </div>
                  </div>

                  <Button 
                    onClick={handleCheckin} 
                    className="w-full h-12"
                    disabled={loading}
                    data-testid="process-checkin-btn"
                  >
                    <UserCheck className="w-5 h-5 mr-2" />
                    Procesar Check-in
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Success Result */}
          {checkinResult && (
            <Card className="card-luxury border-emerald-200 bg-emerald-50/50">
              <CardContent className="pt-6">
                <div className="text-center">
                  <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <CheckCircle className="w-8 h-8 text-emerald-600" />
                  </div>
                  <h3 className="text-xl font-semibold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>
                    Check-in Exitoso
                  </h3>
                  <p className="text-muted-foreground mb-4">
                    El huésped ha sido registrado correctamente
                  </p>
                  <div className="bg-white p-4 rounded-sm text-left">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
                          Habitación
                        </p>
                        <p className="text-2xl font-semibold" style={{ fontFamily: 'Playfair Display, serif' }}>
                          {checkinResult.habitacion?.numero}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
                          Piso
                        </p>
                        <p className="text-2xl font-semibold" style={{ fontFamily: 'Playfair Display, serif' }}>
                          {checkinResult.habitacion?.piso}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {!selectedReserva && !checkinResult && (
            <Card className="card-luxury">
              <CardContent className="py-16 text-center">
                <UserCheck className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">
                  Busque y seleccione una reserva para procesar el check-in
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default CheckinPage;
