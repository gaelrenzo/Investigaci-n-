%% ========================================================================
%  MÉTODO DE SUPERFICIE DE RESPUESTA - SISTEMA DE PISO RADIANTE
%  Procedimiento: Montgomery, "Diseño y Análisis de Experimentos"
%  Software: GNU Octave (no requiere paquetes adicionales)
%
%  x1 = Temperatura de entrada del agua al piso (°C)
%  x2 = Temperatura del aire exterior (°C)
%  y  = Temperatura operativa interior (°C)
%
%  Uso: abrir Octave en esta carpeta y ejecutar:  superficie_respuesta
% =========================================================================
clc; clear; close all;
set(0, 'defaultfigurevisible', 'off');
set(0, 'defaultaxesfontsize', 12, 'defaulttextfontsize', 12, 'defaultlinelinewidth', 1.5);
if ~exist('figuras', 'dir'),    mkdir('figuras');    end
if ~exist('resultados', 'dir'), mkdir('resultados'); end

%% 1) LEER DATOS (variables reales)
D  = dlmread(fullfile('datos', 'datos_MSR.csv'), ',', 1, 0);   % salta encabezado
T1 = D(:,1);   T2 = D(:,2);   y = D(:,3);
n  = numel(y);

%% 2) CODIFICAR VARIABLES:  x = (T - centro) / (DeltaT/2)
c1 = (max(T1) + min(T1))/2;   h1 = (max(T1) - min(T1))/2;
c2 = (max(T2) + min(T2))/2;   h2 = (max(T2) - min(T2))/2;
x1 = (T1 - c1)/h1;
x2 = (T2 - c2)/h2;

%% 3) MATRIZ DEL MODELO DE 2° ORDEN Y COEFICIENTES:  X\y
X    = [ones(n,1) x1 x2 x1.^2 x2.^2 x1.*x2];
coef = X\y;                                    % [b0 b1 b2 b11 b22 b12]
b0 = coef(1); b1 = coef(2); b2 = coef(3);
b11 = coef(4); b22 = coef(5); b12 = coef(6);

yhat = X*coef;
res  = y - yhat;
p    = numel(coef);
SST  = sum((y - mean(y)).^2);
SSE  = sum(res.^2);
SSR  = SST - SSE;
R2   = 1 - SSE/SST;
R2a  = 1 - (SSE/(n-p))/(SST/(n-1));
MSE  = SSE/(n-p);
F    = (SSR/(p-1))/MSE;
pF   = betainc((n-p)/((n-p) + (p-1)*F), (n-p)/2, (p-1)/2);   % p-valor F (sin paquetes)

% Significancia de cada coeficiente (prueba t)
se = sqrt(diag(MSE*inv(X'*X)));
t  = coef./se;
pt = betainc((n-p)./((n-p) + t.^2), (n-p)/2, 0.5);           % p-valor t bilateral

%% 4) FORMA MATRICIAL:  y = b0 + x'b + x'Bx
b = [b1; b2];
B = [b11 b12/2; b12/2 b22];

%% 5) PUNTO ESTACIONARIO:  dy/dx = b + 2Bx = 0  ->  xs = -1/2 * inv(B) * b
xs = -0.5*inv(B)*b;
ys = b0 + 0.5*xs'*b;

%% 6) NATURALEZA DEL PUNTO (eigenvalores de B)
lambda = eig(B);
if all(lambda < 0),     tipo = 'MAXIMO';
elseif all(lambda > 0), tipo = 'MINIMO';
else,                   tipo = 'PUNTO SILLA';
end
dentro = all(abs(xs) <= 1);

%% 7) DECODIFICAR A VARIABLES REALES:  T = centro + (DeltaT/2)*x
T1s = c1 + h1*xs(1);
T2s = c2 + h2*xs(2);

%% 8) MEJOR CONDICIÓN DENTRO DE LA REGIÓN EXPERIMENTAL (-1 <= x <= 1)
[g1, g2] = meshgrid(linspace(-1, 1, 201));
G = b0 + b1*g1 + b2*g2 + b11*g1.^2 + b22*g2.^2 + b12*g1.*g2;
[ymax, k] = max(G(:));
x1m = g1(k);  x2m = g2(k);

%% 9) REPORTE EN PANTALLA Y EN ARCHIVO
nombres = {'b0','b1 (x1)','b2 (x2)','b11 (x1^2)','b22 (x2^2)','b12 (x1x2)'};
fid = fopen(fullfile('resultados', 'resultados.txt'), 'w');
for f = [1 fid]
  fprintf(f, '=== METODO DE SUPERFICIE DE RESPUESTA - PISO RADIANTE ===\n\n');
  fprintf(f, 'Numero de observaciones: n = %d\n\n', n);
  fprintf(f, 'CODIFICACION\n');
  fprintf(f, '  x1 = (T_entrada - %.2f) / %.2f\n', c1, h1);
  fprintf(f, '  x2 = (T_exterior - %.2f) / %.2f\n\n', c2, h2);
  fprintf(f, 'COEFICIENTES (X\\y)\n');
  fprintf(f, '  %-12s %10s %10s %10s %10s\n', 'Termino', 'Coef', 'Error est', 't', 'p-valor');
  for i = 1:p
    fprintf(f, '  %-12s %10.4f %10.4f %10.2f %10.4f\n', nombres{i}, coef(i), se(i), t(i), pt(i));
  end
  fprintf(f, '\nMODELO MATEMATICO (variables codificadas)\n');
  fprintf(f, '  y = %.4f %+.4f x1 %+.4f x2 %+.4f x1^2 %+.4f x2^2 %+.4f x1x2\n\n', coef);
  fprintf(f, 'ANOVA DE LA REGRESION\n');
  fprintf(f, '  %-10s %6s %12s %12s %10s %10s\n', 'Fuente', 'gl', 'SC', 'CM', 'F', 'p-valor');
  fprintf(f, '  %-10s %6d %12.3f %12.3f %10.2f %10.4f\n', 'Regresion', p-1, SSR, SSR/(p-1), F, pF);
  fprintf(f, '  %-10s %6d %12.3f %12.3f\n', 'Error', n-p, SSE, MSE);
  fprintf(f, '  %-10s %6d %12.3f\n', 'Total', n-1, SST);
  fprintf(f, '  R^2 = %.4f   R^2 ajustado = %.4f\n\n', R2, R2a);
  fprintf(f, 'FORMA MATRICIAL\n');
  fprintf(f, '  b = [%.4f ; %.4f]\n', b);
  fprintf(f, '  B = [%.4f  %.4f ; %.4f  %.4f]\n\n', B(1,1), B(1,2), B(2,1), B(2,2));
  fprintf(f, 'PUNTO ESTACIONARIO  xs = -1/2 B^-1 b\n');
  fprintf(f, '  x1s = %.4f   x2s = %.4f\n', xs);
  fprintf(f, '  ys  = %.4f C\n', ys);
  fprintf(f, '  Eigenvalores de B: %.4f  %.4f  ->  %s\n', lambda, tipo);
  if dentro
    fprintf(f, '  El punto esta DENTRO de la region experimental.\n');
  else
    fprintf(f, '  El punto esta FUERA de la region experimental (|x| > 1).\n');
  end
  fprintf(f, '  Decodificado: T_entrada = %.2f C   T_exterior = %.2f C\n\n', T1s, T2s);
  fprintf(f, 'MEJOR CONDICION DENTRO DE LA REGION (-1 <= x <= 1)\n');
  fprintf(f, '  x1 = %.2f -> T_entrada = %.2f C\n', x1m, c1 + h1*x1m);
  fprintf(f, '  x2 = %.2f -> T_exterior = %.2f C\n', x2m, c2 + h2*x2m);
  fprintf(f, '  y maxima estimada = %.2f C\n', ymax);
end
fclose(fid);

%% 10) GRÁFICOS
R1 = c1 + h1*g1;   R2g = c2 + h2*g2;

% Superficie de respuesta
figure;
surf(R1, R2g, G, 'EdgeColor', 'none'); colormap(jet); colorbar; hold on;
plot3(T1, T2, y, 'k.', 'MarkerSize', 4);
xlabel('T entrada agua (°C)'); ylabel('T exterior (°C)'); zlabel('T operativa (°C)');
title('Superficie de respuesta'); view(-35, 25); grid on;
print('-dpng', '-r200', fullfile('figuras', '1_superficie.png'));

% Contorno
figure;
[C, hc] = contourf(R1, R2g, G, floor(min(G(:))):1:ceil(max(G(:)))); colormap(jet); colorbar; hold on;
clabel(C, hc, 'FontSize', 9);
plot(T1, T2, 'k.', 'MarkerSize', 4);
plot(c1 + h1*x1m, c2 + h2*x2m, 'wp', 'MarkerSize', 16, 'MarkerFaceColor', 'w');
xlabel('T entrada agua (°C)'); ylabel('T aire exterior (°C)');
title('Contorno de T operativa (°C)');
print('-dpng', '-r200', fullfile('figuras', '2_contorno.png'));

% Observado vs predicho
figure;
plot(y, yhat, 'b.', 'MarkerSize', 6); hold on;
lim = [min([y; yhat]) max([y; yhat])];
plot(lim, lim, 'r-', 'LineWidth', 2);
xlabel('T operativa observada (°C)'); ylabel('T operativa predicha (°C)');
title(sprintf('Observado vs predicho  (R^2 = %.3f)', R2)); grid on; axis equal; axis([lim lim]);
print('-dpng', '-r200', fullfile('figuras', '3_observado_vs_predicho.png'));

% Residuos
figure;
subplot(1,2,1);
plot(yhat, res, 'b.', 'MarkerSize', 6); hold on; plot(xlim, [0 0], 'r-');
xlabel('Valor predicho (°C)'); ylabel('Residuo (°C)'); title('Residuos vs predichos'); grid on;
subplot(1,2,2);
hist(res, 30); xlabel('Residuo (°C)'); ylabel('Frecuencia'); title('Histograma de residuos'); grid on;
print('-dpng', '-r200', fullfile('figuras', '4_residuos.png'));

disp(' ');
disp('Listo: revisa las carpetas "resultados" y "figuras".');
