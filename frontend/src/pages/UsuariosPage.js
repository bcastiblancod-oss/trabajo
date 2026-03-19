import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { getUsuarios, createUsuario, updateUsuario, deleteUsuario } from '../services/api';
import { Card, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../components/ui/dialog';
import { Users, Plus, Pencil, Trash2, AlertTriangle } from 'lucide-react';
import { toast } from 'sonner';

const UsuariosPage = () => {
  const { token, user } = useAuth();
  const [usuarios, setUsuarios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createModal, setCreateModal] = useState(false);
  const [editModal, setEditModal] = useState(false);
  const [deleteModal, setDeleteModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    nombre_completo: '',
    documento: '',
    telefono: '',
    rol: 'huesped'
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const data = await getUsuarios(token);
      setUsuarios(data);
    } catch (error) {
      toast.error('Error al cargar usuarios');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async () => {
    try {
      await createUsuario(token, formData);
      toast.success('Usuario creado exitosamente');
      setCreateModal(false);
      resetForm();
      loadData();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const handleUpdate = async () => {
    try {
      await updateUsuario(token, selectedUser.id, {
        nombre_completo: formData.nombre_completo,
        telefono: formData.telefono,
        activo: formData.activo
      });
      toast.success('Usuario actualizado');
      setEditModal(false);
      loadData();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const handleDelete = async () => {
    try {
      await deleteUsuario(token, selectedUser.id);
      toast.success('Usuario desactivado');
      setDeleteModal(false);
      loadData();
    } catch (error) {
      toast.error(error.message);
    }
  };

  const openEditModal = (usuario) => {
    setSelectedUser(usuario);
    setFormData({
      ...formData,
      nombre_completo: usuario.nombre_completo,
      telefono: usuario.telefono || '',
      activo: usuario.activo
    });
    setEditModal(true);
  };

  const resetForm = () => {
    setFormData({
      email: '',
      password: '',
      nombre_completo: '',
      documento: '',
      telefono: '',
      rol: 'huesped'
    });
  };

  const getRolBadge = (rol) => {
    const badges = {
      administrador: 'bg-amber-100 text-amber-800',
      recepcionista: 'bg-blue-100 text-blue-800',
      huesped: 'bg-emerald-100 text-emerald-800'
    };
    const labels = {
      administrador: 'Admin',
      recepcionista: 'Recepción',
      huesped: 'Huésped'
    };
    return (
      <span className={`${badges[rol]} px-3 py-1 rounded-full text-xs font-medium`}>
        {labels[rol]}
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
    <div className="animate-fade-in" data-testid="usuarios-page">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-8">
        <div>
          <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-2">
            Administración
          </p>
          <h1 className="text-3xl font-medium" style={{ fontFamily: 'Playfair Display, serif' }}>
            Usuarios
          </h1>
        </div>
        <Button
          onClick={() => setCreateModal(true)}
          className="bg-primary text-primary-foreground h-12 px-6 rounded-sm"
          data-testid="create-user-btn"
        >
          <Plus className="w-4 h-4 mr-2" />
          Nuevo Usuario
        </Button>
      </div>

      <Card className="card-luxury">
        <CardContent className="p-0">
          {usuarios.length === 0 ? (
            <div className="text-center py-16">
              <Users className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No hay usuarios</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-stone-50/50">
                  <tr>
                    <th className="text-left py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Usuario</th>
                    <th className="text-left py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Documento</th>
                    <th className="text-left py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Rol</th>
                    <th className="text-left py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Estado</th>
                    <th className="text-right py-4 px-6 text-xs uppercase tracking-widest font-semibold text-muted-foreground">Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {usuarios.map((usuario) => (
                    <tr key={usuario.id} className="border-b border-stone-100 last:border-0 hover:bg-stone-50/30 transition-colors">
                      <td className="py-4 px-6">
                        <div>
                          <p className="font-medium">{usuario.nombre_completo}</p>
                          <p className="text-sm text-muted-foreground">{usuario.email}</p>
                        </div>
                      </td>
                      <td className="py-4 px-6 text-sm">{usuario.documento}</td>
                      <td className="py-4 px-6">{getRolBadge(usuario.rol)}</td>
                      <td className="py-4 px-6">
                        <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                          usuario.activo ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {usuario.activo ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>
                      <td className="py-4 px-6 text-right">
                        <div className="flex justify-end gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openEditModal(usuario)}
                            data-testid={`edit-user-${usuario.id}`}
                          >
                            <Pencil className="w-4 h-4" />
                          </Button>
                          {usuario.id !== user?.id && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => { setSelectedUser(usuario); setDeleteModal(true); }}
                              className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              data-testid={`delete-user-${usuario.id}`}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          )}
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

      {/* Create Modal */}
      <Dialog open={createModal} onOpenChange={(open) => { setCreateModal(open); if (!open) resetForm(); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Playfair Display, serif' }}>
              Nuevo Usuario
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Nombre completo</Label>
              <Input
                value={formData.nombre_completo}
                onChange={(e) => setFormData({...formData, nombre_completo: e.target.value})}
                className="mt-1"
                data-testid="new-user-name"
              />
            </div>
            <div>
              <Label>Email</Label>
              <Input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="mt-1"
                data-testid="new-user-email"
              />
            </div>
            <div>
              <Label>Contraseña</Label>
              <Input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                className="mt-1"
                data-testid="new-user-password"
              />
            </div>
            <div>
              <Label>Documento</Label>
              <Input
                value={formData.documento}
                onChange={(e) => setFormData({...formData, documento: e.target.value})}
                className="mt-1"
              />
            </div>
            <div>
              <Label>Teléfono</Label>
              <Input
                value={formData.telefono}
                onChange={(e) => setFormData({...formData, telefono: e.target.value})}
                className="mt-1"
              />
            </div>
            <div>
              <Label>Rol</Label>
              <Select value={formData.rol} onValueChange={(v) => setFormData({...formData, rol: v})}>
                <SelectTrigger className="mt-1">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="huesped">Huésped</SelectItem>
                  <SelectItem value="recepcionista">Recepcionista</SelectItem>
                  <SelectItem value="administrador">Administrador</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => { setCreateModal(false); resetForm(); }}>Cancelar</Button>
            <Button onClick={handleCreate} data-testid="confirm-create-user">Crear</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Modal */}
      <Dialog open={editModal} onOpenChange={setEditModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle style={{ fontFamily: 'Playfair Display, serif' }}>
              Editar Usuario
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div>
              <Label>Nombre completo</Label>
              <Input
                value={formData.nombre_completo}
                onChange={(e) => setFormData({...formData, nombre_completo: e.target.value})}
                className="mt-1"
              />
            </div>
            <div>
              <Label>Teléfono</Label>
              <Input
                value={formData.telefono}
                onChange={(e) => setFormData({...formData, telefono: e.target.value})}
                className="mt-1"
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={formData.activo}
                onChange={(e) => setFormData({...formData, activo: e.target.checked})}
                className="rounded"
              />
              <Label>Usuario activo</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditModal(false)}>Cancelar</Button>
            <Button onClick={handleUpdate}>Guardar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Modal */}
      <Dialog open={deleteModal} onOpenChange={setDeleteModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-red-600">
              <AlertTriangle className="w-5 h-5" />
              Desactivar Usuario
            </DialogTitle>
            <DialogDescription>
              ¿Está seguro de desactivar al usuario {selectedUser?.nombre_completo}?
              El usuario no podrá acceder al sistema.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteModal(false)}>Cancelar</Button>
            <Button variant="destructive" onClick={handleDelete}>Desactivar</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default UsuariosPage;
