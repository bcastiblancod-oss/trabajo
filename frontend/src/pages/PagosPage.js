import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getPagos, createPago, getReservas } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { CreditCard, Plus } from 'lucide-react';
import { toast } from 'sonner';

const PagosPage = () => {
  const { token, hasRole } = useAuth();
  const [pagos, setPagos] = useState([]);
  const [reservas, setReservas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createModal, setCreateModal] = useState(false);
  const [formData, setFormData] = useState({
    reserva_id: '',
    monto: '',
    metodo_pago: 'efectivo',
    referencia: '',
    notas: ''
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [pagosData, reservasData] = await Promise.all([
        getPagos(token),
        getReservas(token, { estado: 'confirmada' })
      ]);
      setPagos(pagosData);
      setReservas(reservasData);
    } catch (error) {
      toast.error('Error al cargar pagos');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePago = async () => {
    try {
      await createPago(token, {
        ...formData,
        monto: parseFloat(formData.monto)
      });
      toast.success('Pago registrado exitosamente');
      setCreateModal(false);
      setFormData({ reserva_id: '', monto: '', metodo_pago: 'efectivo', referencia: '', notas: '' });
      loadData();
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

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('es-CO', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getMetodoBadge = (metodo) => {
    const badges = {
      tarjeta_credito: 'bg-blue-100 text-blue-800',
      tarjeta_debito: 'bg-purple-100 text-purple-800',
      efectivo: 'bg-emerald-100 text-emerald-800',
      transferencia: 'bg-amber-100 text-amber-800'
    };
    const labels = {
      tarjeta_credito: 'T. Crédito',
      tarjeta_debito: 'T. Débito',
      efectivo: 'Efectivo',
      transferencia: 'Transferencia'
    };
    return (
      <span className={`${badges[metodo]} px-3 py-1 rounded-full text-xs font-medium`}>
        {labels[metodo]}
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
    <div className="animate-fade-in" data-testid="pagos-page">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
        <div>
          <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-2">
            Gestión
          </p>
          <h1 className="text-3xl font-medium" style={{ fontFamily: 'Playfair Display, serif' }}>
            Pagos
          </h1>
        </div>
        {hasRole('administrador', 'recepcionista') && (
          <Button
            onClick={() => setCreateModal(true)}
            className="bg-primary text-primary-foreground h-12 px-6 rounded-sm"
            data-testid="register-payment-btn"
          >
            <Plus className="w-4 h-4 mr-2" />
            Registrar Pago
          </Button>
        )}
      </div>

      <Card className="card-luxury">
        <CardContent className="p-0">
          {pagos.length === 0 ? (
            <div className="text-center py-16">
              <CreditCard className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No hay pagos registrados</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-stone-50/50">
                  <tr>
                    <th className="text-left py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Comprobante</th>
                    <th className="text-left py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Fecha</th>
                    <th className="text-left py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Método</th>
                    <th className="text-left py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Referencia</th>
                    <th className="text-right py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Monto</th>
                  </tr>
                </thead>
                <tbody>
                  {pagos.map((pago) => (
                    <tr key={pago.id} className="border-b border-stone-100 last:border-0 hover:bg-stone-50/30 transition-colors">
                      <td className="py-4 px-6 font-medium">{pago.comprobante}</td>
                      <td className="py-4 px-6 text-sm text-muted-foreground">{formatDate(pago.fecha)}</td>
                      <td className="py-4 px-6">{getMetodoBadge(pago.metodo_pago)}</td>
                      <td className="py-4 px-6 text-sm">{pago.referencia || '-'}</td>
                      <td className="py-4 px-6 text-right font-semibold">{formatCurrency(pago.monto)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Modal */}
      <Dialog open={createModal} onOpenChange={setCreateModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Playfair Display, serif' }}>
              Registrar Pago
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Reserva</Label>
              <Select value={formData.reserva_id} onValueChange={(v) => setFormData({...formData, reserva_id: v})}>
                <SelectTrigger className="mt-1" data-testid="payment-reserva-select">
                  <SelectValue placeholder="Seleccione una reserva" />
                </SelectTrigger>
                <SelectContent>
                  {reservas.map((reserva) => (
                    <SelectItem key={reserva.id} value={reserva.id}>
                      {reserva.codigo} - {reserva.huesped?.nombre_completo}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Monto</Label>
              <Input
                type="number"
                min="0"
                value={formData.monto}
                onChange={(e) => setFormData({...formData, monto: e.target.value})}
                className="mt-1"
                placeholder="0"
                data-testid="payment-amount-input"
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
            <div>
              <Label>Referencia (opcional)</Label>
              <Input
                value={formData.referencia}
                onChange={(e) => setFormData({...formData, referencia: e.target.value})}
                className="mt-1"
                placeholder="Número de transacción"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateModal(false)}>Cancelar</Button>
            <Button 
              onClick={handleCreatePago}
              disabled={!formData.reserva_id || !formData.monto}
              data-testid="confirm-payment-btn"
            >
              Registrar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default PagosPage;
