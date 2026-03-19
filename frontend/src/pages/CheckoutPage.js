import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getReservas, getConsumos, addConsumo, processCheckout } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { ClipboardCheck, Plus, Receipt, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';

const CheckoutPage = () => {
  const { token } = useAuth();
  const [reservasCheckedIn, setReservasCheckedIn] = useState([]);
  const [selectedReserva, setSelectedReserva] = useState(null);
  const [consumos, setConsumos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [addConsumoModal, setAddConsumoModal] = useState(false);
  const [checkoutResult, setCheckoutResult] = useState(null);
  const [consumoForm, setConsumoForm] = useState({
    descripcion: '',
    cantidad: 1,
    precio_unitario: 0,
    categoria: 'minibar'
  });

  useEffect(() => {
    loadReservas();
  }, []);

  const loadReservas = async () => {
    try {
      const data = await getReservas(token, { estado: 'checked_in' });
      setReservasCheckedIn(data);
    } catch (error) {
      toast.error('Error al cargar reservas');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectReserva = async (reserva) => {
    setSelectedReserva(reserva);
    setCheckoutResult(null);
    try {
      const consumosData = await getConsumos(token, reserva.id);
      setConsumos(consumosData);
    } catch (error) {
      setConsumos([]);
    }
  };

  const handleAddConsumo = async () => {
    try {
      await addConsumo(token, {
        reserva_id: selectedReserva.id,
        ...consumoForm
      });
      toast.success('Consumo agregado');
      setAddConsumoModal(false);
      setConsumoForm({ descripcion: '', cantidad: 1, precio_unitario: 0, categoria: 'minibar' });
      const consumosData = await getConsumos(token, selectedReserva.id);
      setConsumos(consumosData);
    } catch (error) {
      toast.error(error.message);
    }
  };

  const handleCheckout = async () => {
    try {
      const result = await processCheckout(token, { reserva_id: selectedReserva.id });
      setCheckoutResult(result);
      toast.success('Check-out realizado exitosamente');
      loadReservas();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0
    }).format(value);
  };

  const totalConsumos = consumos.reduce((sum, c) => sum + c.subtotal, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="animate-fade-in" data-testid="checkout-page">
      <div className="mb-8">
        <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-2">
          Recepción
        </p>
        <h1 className="text-3xl font-medium" style={{ fontFamily: 'Playfair Display, serif' }}>
          Check-out
        </h1>
      </div>

      {checkoutResult ? (
        /* Checkout Success */
        <Card className="card-luxury max-w-2xl mx-auto">
          <CardContent className="pt-6">
            <div className="text-center mb-8">
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-8 h-8 text-emerald-600" />
              </div>
              <h3 className="text-2xl font-semibold mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>
                Check-out Completado
              </h3>
              <p className="text-muted-foreground">
                Factura generada correctamente
              </p>
            </div>

            <div className="bg-stone-50 p-6 rounded-sm space-y-4">
              <div className="flex justify-between py-2 border-b border-stone-200">
                <span className="text-muted-foreground">Alojamiento</span>
                <span className="font-medium">{formatCurrency(checkoutResult.subtotal_habitacion)}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-stone-200">
                <span className="text-muted-foreground">Servicios adicionales</span>
                <span className="font-medium">{formatCurrency(checkoutResult.subtotal_servicios)}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-stone-200">
                <span className="text-muted-foreground">Consumos</span>
                <span className="font-medium">{formatCurrency(checkoutResult.subtotal_consumos)}</span>
              </div>
              <div className="flex justify-between py-2 border-b border-stone-200">
                <span className="text-muted-foreground">IVA (19%)</span>
                <span className="font-medium">{formatCurrency(checkoutResult.impuestos)}</span>
              </div>
              <div className="flex justify-between py-4">
                <span className="text-xl font-semibold">Total</span>
                <span className="text-2xl font-semibold" style={{ fontFamily: 'Playfair Display, serif' }}>
                  {formatCurrency(checkoutResult.total)}
                </span>
              </div>
            </div>

            <Button 
              onClick={() => { setSelectedReserva(null); setCheckoutResult(null); }}
              className="w-full mt-6"
            >
              Nuevo Check-out
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Reservations List */}
          <Card className="card-luxury">
            <CardHeader>
              <CardTitle className="text-lg">Huéspedes Activos</CardTitle>
            </CardHeader>
            <CardContent>
              {reservasCheckedIn.length === 0 ? (
                <p className="text-center text-muted-foreground py-8">
                  No hay huéspedes con check-in activo
                </p>
              ) : (
                <div className="space-y-2">
                  {reservasCheckedIn.map((reserva) => (
                    <div
                      key={reserva.id}
                      onClick={() => handleSelectReserva(reserva)}
                      className={`p-4 border rounded-sm cursor-pointer transition-all ${
                        selectedReserva?.id === reserva.id
                          ? 'border-primary bg-primary/5'
                          : 'border-stone-200 hover:border-stone-300'
                      }`}
                      data-testid={`checkout-reserva-${reserva.codigo}`}
                    >
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="font-medium">{reserva.habitacion?.numero}</p>
                          <p className="text-sm text-muted-foreground">
                            {reserva.huesped?.nombre_completo}
                          </p>
                        </div>
                        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full">
                          Check-in
                        </span>
                      </div>
                      <p className="text-xs text-muted-foreground mt-2">
                        Salida: {reserva.fecha_checkout}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Details & Consumos */}
          <div className="lg:col-span-2 space-y-6">
            {selectedReserva ? (
              <>
                {/* Reservation Details */}
                <Card className="card-luxury">
                  <CardHeader>
                    <div className="flex justify-between items-center">
                      <CardTitle className="text-lg">
                        Habitación {selectedReserva.habitacion?.numero}
                      </CardTitle>
                      <span className="text-sm text-muted-foreground">{selectedReserva.codigo}</span>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
                          Huésped
                        </p>
                        <p className="font-medium mt-1">{selectedReserva.huesped?.nombre_completo}</p>
                      </div>
                      <div>
                        <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
                          Fecha salida
                        </p>
                        <p className="font-medium mt-1">{selectedReserva.fecha_checkout}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Consumos */}
                <Card className="card-luxury">
                  <CardHeader>
                    <div className="flex justify-between items-center">
                      <CardTitle className="text-lg">Consumos</CardTitle>
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => setAddConsumoModal(true)}
                        data-testid="add-consumo-btn"
                      >
                        <Plus className="w-4 h-4 mr-1" />
                        Agregar
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent>
                    {consumos.length === 0 ? (
                      <p className="text-center text-muted-foreground py-4">
                        Sin consumos adicionales
                      </p>
                    ) : (
                      <div className="space-y-2">
                        {consumos.map((consumo) => (
                          <div key={consumo.id} className="flex justify-between p-3 bg-stone-50 rounded-sm">
                            <div>
                              <p className="font-medium">{consumo.descripcion}</p>
                              <p className="text-xs text-muted-foreground">
                                {consumo.categoria} • x{consumo.cantidad}
                              </p>
                            </div>
                            <span className="font-medium">{formatCurrency(consumo.subtotal)}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>

                {/* Summary */}
                <Card className="card-luxury">
                  <CardContent className="pt-6">
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Alojamiento</span>
                        <span>{formatCurrency(selectedReserva.precio_habitacion)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Servicios</span>
                        <span>{formatCurrency(selectedReserva.precio_servicios)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Consumos</span>
                        <span>{formatCurrency(totalConsumos)}</span>
                      </div>
                      <div className="flex justify-between pt-3 border-t">
                        <span className="font-medium">Subtotal</span>
                        <span className="font-medium">
                          {formatCurrency(selectedReserva.precio_habitacion + selectedReserva.precio_servicios + totalConsumos)}
                        </span>
                      </div>
                    </div>

                    <Button 
                      onClick={handleCheckout}
                      className="w-full mt-6 h-12"
                      data-testid="process-checkout-btn"
                    >
                      <Receipt className="w-5 h-5 mr-2" />
                      Procesar Check-out
                    </Button>
                  </CardContent>
                </Card>
              </>
            ) : (
              <Card className="card-luxury">
                <CardContent className="py-16 text-center">
                  <ClipboardCheck className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">
                    Seleccione un huésped para procesar el check-out
                  </p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      )}

      {/* Add Consumo Modal */}
      <Dialog open={addConsumoModal} onOpenChange={setAddConsumoModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Agregar Consumo</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Categoría</Label>
              <Select value={consumoForm.categoria} onValueChange={(v) => setConsumoForm({...consumoForm, categoria: v})}>
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="minibar">Minibar</SelectItem>
                  <SelectItem value="lavanderia">Lavandería</SelectItem>
                  <SelectItem value="telefono">Teléfono</SelectItem>
                  <SelectItem value="restaurante">Restaurante</SelectItem>
                  <SelectItem value="spa">Spa</SelectItem>
                  <SelectItem value="otro">Otro</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Descripción</Label>
              <Input
                value={consumoForm.descripcion}
                onChange={(e) => setConsumoForm({...consumoForm, descripcion: e.target.value})}
                className="mt-1"
                placeholder="Ej: Agua mineral"
                data-testid="consumo-descripcion"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Cantidad</Label>
                <Input
                  type="number"
                  min="1"
                  value={consumoForm.cantidad}
                  onChange={(e) => setConsumoForm({...consumoForm, cantidad: parseInt(e.target.value)})}
                  className="mt-1"
                />
              </div>
              <div>
                <Label>Precio unitario</Label>
                <Input
                  type="number"
                  min="0"
                  value={consumoForm.precio_unitario}
                  onChange={(e) => setConsumoForm({...consumoForm, precio_unitario: parseFloat(e.target.value)})}
                  className="mt-1"
                  data-testid="consumo-precio"
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddConsumoModal(false)}>Cancelar</Button>
            <Button onClick={handleAddConsumo} data-testid="save-consumo-btn">Agregar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CheckoutPage;
