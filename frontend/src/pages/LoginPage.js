import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { toast } from 'sonner';
import { BedDouble, Loader2 } from 'lucide-react';

const LoginPage = () => {
  const { login, register } = useAuth();
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    nombre_completo: '',
    documento: '',
    telefono: ''
  });

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (isLogin) {
        await login(formData.email, formData.password);
        toast.success('Bienvenido al sistema');
      } else {
        await register(formData);
        toast.success('Registro exitoso. Ahora puede iniciar sesión');
        setIsLogin(true);
        setFormData({ ...formData, password: '' });
      }
    } catch (error) {
      toast.error(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex" data-testid="login-page">
      {/* Left Panel - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 lg:p-16 bg-[#fcfaf8]">
        <div className="w-full max-w-md animate-fade-in">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-12">
            <div className="w-12 h-12 bg-primary rounded-sm flex items-center justify-center">
              <BedDouble className="w-6 h-6 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-xl font-semibold tracking-tight" style={{ fontFamily: 'Playfair Display, serif' }}>
                Hotel Imperium
              </h1>
              <p className="text-xs text-muted-foreground tracking-widest uppercase">Boutique Hotel</p>
            </div>
          </div>

          {/* Title */}
          <h2 className="text-3xl font-medium mb-2" style={{ fontFamily: 'Playfair Display, serif' }}>
            {isLogin ? 'Bienvenido' : 'Crear cuenta'}
          </h2>
          <p className="text-muted-foreground mb-8">
            {isLogin 
              ? 'Ingrese sus credenciales para acceder al sistema' 
              : 'Complete el formulario para registrarse como huésped'}
          </p>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {!isLogin && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="nombre_completo" className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
                    Nombre completo
                  </Label>
                  <Input
                    id="nombre_completo"
                    name="nombre_completo"
                    value={formData.nombre_completo}
                    onChange={handleChange}
                    required={!isLogin}
                    className="h-12 border-0 border-b border-input rounded-none px-0 focus-visible:ring-0 focus-visible:border-primary"
                    data-testid="register-name-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="documento" className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
                    Documento de identidad
                  </Label>
                  <Input
                    id="documento"
                    name="documento"
                    value={formData.documento}
                    onChange={handleChange}
                    required={!isLogin}
                    className="h-12 border-0 border-b border-input rounded-none px-0 focus-visible:ring-0 focus-visible:border-primary"
                    data-testid="register-document-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="telefono" className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
                    Teléfono
                  </Label>
                  <Input
                    id="telefono"
                    name="telefono"
                    value={formData.telefono}
                    onChange={handleChange}
                    className="h-12 border-0 border-b border-input rounded-none px-0 focus-visible:ring-0 focus-visible:border-primary"
                    data-testid="register-phone-input"
                  />
                </div>
              </>
            )}

            <div className="space-y-2">
              <Label htmlFor="email" className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
                Correo electrónico
              </Label>
              <Input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                required
                className="h-12 border-0 border-b border-input rounded-none px-0 focus-visible:ring-0 focus-visible:border-primary"
                data-testid="login-email-input"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password" className="text-xs uppercase tracking-widest font-semibold text-muted-foreground">
                Contraseña
              </Label>
              <Input
                id="password"
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                required
                className="h-12 border-0 border-b border-input rounded-none px-0 focus-visible:ring-0 focus-visible:border-primary"
                data-testid="login-password-input"
              />
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full h-12 bg-primary text-primary-foreground rounded-sm font-medium tracking-wide hover:bg-primary/90 transition-all duration-300"
              data-testid="login-submit-btn"
            >
              {loading ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                isLogin ? 'Iniciar sesión' : 'Registrarse'
              )}
            </Button>
          </form>

          {/* Toggle */}
          <p className="text-center mt-8 text-muted-foreground">
            {isLogin ? '¿No tiene cuenta?' : '¿Ya tiene cuenta?'}{' '}
            <button
              type="button"
              onClick={() => setIsLogin(!isLogin)}
              className="text-primary hover:text-secondary font-medium transition-colors"
              data-testid="toggle-auth-mode"
            >
              {isLogin ? 'Regístrese aquí' : 'Inicie sesión'}
            </button>
          </p>

          {/* Demo credentials */}
          <div className="mt-12 p-4 bg-stone-50 rounded-sm">
            <p className="text-xs uppercase tracking-widest font-semibold text-muted-foreground mb-3">
              Credenciales de prueba
            </p>
            <div className="space-y-1 text-sm text-muted-foreground">
              <p><span className="font-medium text-foreground">Admin:</span> admin@hotelimperium.com / Admin123!</p>
              <p><span className="font-medium text-foreground">Recepción:</span> recepcion@hotelimperium.com / Recep123!</p>
              <p><span className="font-medium text-foreground">Huésped:</span> huesped@test.com / Huesped123!</p>
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Image */}
      <div className="hidden lg:block lg:w-1/2 login-bg relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary/90 to-primary/70" />
        <div className="absolute inset-0 flex flex-col items-center justify-center text-white p-16">
          <h2 className="text-5xl font-medium mb-6 text-center" style={{ fontFamily: 'Playfair Display, serif' }}>
            Sistema de Gestión
          </h2>
          <p className="text-xl text-white/80 text-center max-w-md leading-relaxed">
            Administre reservas, habitaciones y huéspedes con elegancia y eficiencia
          </p>
          <div className="mt-12 grid grid-cols-3 gap-8 text-center">
            <div>
              <p className="text-4xl font-semibold" style={{ fontFamily: 'Playfair Display, serif' }}>24</p>
              <p className="text-sm text-white/60 mt-1">Habitaciones</p>
            </div>
            <div>
              <p className="text-4xl font-semibold" style={{ fontFamily: 'Playfair Display, serif' }}>3</p>
              <p className="text-sm text-white/60 mt-1">Categorías</p>
            </div>
            <div>
              <p className="text-4xl font-semibold" style={{ fontFamily: 'Playfair Display, serif' }}>24/7</p>
              <p className="text-sm text-white/60 mt-1">Servicio</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
