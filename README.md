# AgroData V2

**Inteligencia territorial para tomar mejores decisiones agr?colas en Per?.**

Aplicaci?n local con Next.js, FastAPI y PostgreSQL. Convierte las series JSON suministradas en consultas persistentes, rankings por cultivo y comparaciones de rendimiento. Identidad visual basada en el logo original, verde bosque `#14532d`, lima `#84cc16` y fondo `#f9fafb`.

## Estado de entrega

- Dashboard, rankings, evoluci?n, producci?n anual y explorador implementados.
- Registro con correo y contrase?a, inicio y cierre de sesi?n; contrase?as Argon2 y cookie HttpOnly.
- Flujo de acceso con Google implementado; requiere credenciales del propietario y una prueba real de consentimiento.
- PostgreSQL local inicializado en `127.0.0.1:55432`, migraci?n `001` aplicada y datos importados.
- Next.js compila para producci?n. Cinco pruebas de integraci?n contra PostgreSQL pasan.
- No incluye entrenamiento ni ejecuci?n de un archivo XGBoost: muestra predicciones ya calculadas en los JSON. R? y WMAPE quedan sin declarar porque no se entregaron m?tricas verificables.
- No se ha realizado una inspecci?n visual en navegador automatizado. La validaci?n incluye compilaci?n, pruebas de API y consultas HTTP.

## Arquitectura

```text
Navegador ? Next.js :3000 ? /backend/* ? FastAPI :8000 ? PostgreSQL :55432
                                                 ?
JSON originales ? importaci?n transaccional ? tablas relacionales
Google OAuth ? callback FastAPI ? cookie de sesi?n ? Dashboard
```

| Capa | Tecnolog?a |
| --- | --- |
| Interfaz | Next.js 15, React 19, TypeScript, App Router |
| Dise?o | Tailwind CSS 4, componentes Radix/shadcn, Lucide, Framer Motion |
| Visualizaci?n | Recharts; rendimiento y producci?n con ejes independientes |
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2, Psycopg 3 |
| Persistencia | PostgreSQL 17; Alembic |
| Autenticaci?n | Argon2, JWT HS256 en cookie HttpOnly, OAuth de Google |

## Inicio local en este equipo

Los paquetes est?n instalados en `backend/.venv` y `frontend/node_modules`. La configuraci?n privada est? en `backend/.env`, fuera del control de versiones.

```powershell
# Desde la ra?z; inicia PostgreSQL si est? detenido y abre los servidores en segundo plano.
powershell -ExecutionPolicy Bypass -File scripts/start.ps1
```

Abre **http://localhost:3000** y crea tu cuenta. No hay contrase?as de usuario predefinidas. La documentaci?n interactiva de la API est? en **http://localhost:8000/docs**.

El script reutiliza los servidores que responden, compila si faltan artefactos y verifica las respuestas HTTP antes de anunciar que est? listo. Para recompilar cambios usa `powershell -ExecutionPolicy Bypass -File scripts/start.ps1 -Rebuild`. Desarrollo utiliza `.next/` y producci?n `.next-production/` para evitar que una ejecuci?n borre los artefactos de la otra. Los registros del script quedan en `api.log`, `api-error.log`, `frontend.log` y `frontend-error.log`. Los procesos se inician con ventanas ocultas. Para trabajo diario se recomienda usar dos terminales, como se describe abajo; Ctrl+C detiene cada servidor.

## Instalaci?n reproducible

Requisitos: Node.js 22 o superior, npm, Python 3.11 o superior y PostgreSQL 17 o Docker Compose. Los puertos 3000, 8000 y 55432 deben estar libres. El puerto 55432 evita un bloqueo de Windows observado en 5433.

### 1. Base de datos

Opci?n Docker, desde la ra?z:

```powershell
docker compose up -d db
```

Alternativamente, crea una base `agrodata` y un rol `agrodata` en tu PostgreSQL. La instancia aislada de este equipo guarda sus archivos en `.pgdata/` y escucha solamente en IPv4 local. Utiliza autenticaci?n `scram-sha-256`.

```powershell
& 'C:/Program Files/PostgreSQL/17/bin/pg_ctl.exe' -D .pgdata -l postgres.log -o '-p 55432 -h 127.0.0.1' start
# Para detener exclusivamente esta instancia:
& 'C:/Program Files/PostgreSQL/17/bin/pg_ctl.exe' -D .pgdata stop
```

Las credenciales `agrodata:agrodata` son exclusivamente de desarrollo local. Para otra instalaci?n, establece una contrase?a propia tanto en PostgreSQL como en `DATABASE_URL`; Docker acepta `POSTGRES_PASSWORD`.

### 2. Backend y configuraci?n

```powershell
python -m venv backend/.venv
& backend/.venv/Scripts/python.exe -m pip install -r backend/requirements.lock.txt
Copy-Item backend/.env.example backend/.env
```

Edita `.env` antes de iniciar: genera un `JWT_SECRET` aleatorio de al menos 32 caracteres. No reemplaces el `.env` existente si ya est? configurado.

| Variable | Uso |
| --- | --- |
| `DATABASE_URL` | `postgresql+psycopg://agrodata:agrodata@127.0.0.1:55432/agrodata` |
| `JWT_SECRET` | Firma de sesi?n; mantener privada y estable entre reinicios |
| `FRONTEND_URL` | `http://localhost:3000` |
| `GOOGLE_CLIENT_ID` | Identificador OAuth de cliente web |
| `GOOGLE_CLIENT_SECRET` | Secreto OAuth, solo backend |
| `GOOGLE_REDIRECT_URI` | `http://localhost:8000/auth/google/callback` |

### 3. Migraciones e importaci?n

```powershell
Set-Location backend
& .venv/Scripts/python.exe -m alembic upgrade head
& .venv/Scripts/python.exe -m app.import_data
& .venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

El importador sustituye ?nicamente `observations` y `districts` dentro de una transacci?n; conserva usuarios. Puede repetirse sin duplicados. Si un archivo es inv?lido, la transacci?n se revierte. Para producci?n, respalda la base antes de reemplazar informaci?n.

La migraci?n inicial crea tablas, claves ?nicas e ?ndices. Consulta la versi?n con `python -m alembic current`. `python -m alembic downgrade base` elimina todas las tablas, incluidas las cuentas: ?salo solo para reinicializaciones deliberadas.

### 4. Frontend

En otra terminal, desde la ra?z:

```powershell
Set-Location frontend
npm ci
npm run build
npm run start
# Desarrollo con recarga:
# npm run dev
```

El proxy de Next.js dirige `/backend/*` a `127.0.0.1:8000`. Accede mediante **localhost**, tambi?n durante OAuth, para mantener las cookies del mismo hostname. Las p?ginas se sirven localmente; Google necesita conexi?n a Internet.

## Acceso con Google

1. Crea o selecciona un proyecto en Google Cloud y configura la pantalla de consentimiento para AgroData.
2. Crea un cliente OAuth de tipo **Aplicaci?n web**.
3. Registra exactamente `http://localhost:8000/auth/google/callback` como URI de redirecci?n autorizada. Si se solicita un origen JavaScript, utiliza `http://localhost:3000`.
4. Copia el Client ID y Client Secret a `backend/.env`. A?ade tu correo como usuario de prueba si la aplicaci?n est? en modo de pruebas.
5. Reinicia FastAPI, abre `http://localhost:3000` y selecciona Google.

El flujo solicita solamente `openid email profile`, verifica `state`, firma RS256, emisor, audiencia y expiraci?n del ID token, y el correo verificado de Google. No solicita acceso a Drive. Las cuentas de Google se identifican por `sub`; no se vinculan autom?ticamente a una cuenta local con el mismo correo. En ese caso se solicita entrar con la contrase?a existente.

Referencia: [OpenID Connect de Google](https://developers.google.com/identity/openid-connect/openid-connect). Sin las credenciales del proyecto no es posible completar una prueba real de inicio de sesi?n con Google. Si no se configuran, el endpoint devuelve un mensaje expl?cito con estado 503.

## Datos y reglas de negocio

| Archivo | Registros | Tratamiento |
| --- | ---: | --- |
| `historial_anual.json` | 238 | Serie nacional hist?rica |
| `historial_departamento.json` | 4.193 | Serie hist?rica por departamento |
| `predicciones_anual.json` | 40 | Proyecciones nacionales de 2026 y 2027 |
| `predicciones_departamento.json` | 734 | Proyecciones departamentales |
| `scoring_distrito.json` | 12.050 | Ranking territorial autoritativo |
| `top_distritos_por_cultivo.json` | 20 grupos | Validado contra los distritos; top derivado por consulta |
| `metadata.json` | No suministrado | Metadatos derivados mediante consultas SQL |

Los originales permanecen en la ra?z y no se publican como datos est?ticos del frontend. El sistema utiliza PostgreSQL durante las consultas.

- **Codificaci?n del a?o:** los archivos contienen una clave de a?o da?ada (`A?O`). El importador la reconoce por su prefijo y valor entero, y guarda un campo `year` limpio.
- **Agregados:** la serie nacional utiliza `department=''`. Nunca se suma con las series departamentales: eso duplicar?a producci?n y registros. El rendimiento entregado se conserva; no se recalcula a partir de producci?n agregada.
- **Filtros en cascada:** los departamentos proceden exclusivamente del historial del cultivo seleccionado. Cambiar cultivo restablece el departamento y la p?gina.
- **Base de comparaci?n:** media aritm?tica de los cinco ?ltimos a?os hist?ricos disponibles por cultivo y ?mbito. Con el conjunto actual, 2022?2026. Si faltan a?os, se promedian los disponibles y se muestran sus a?os exactos.
- **Variaci?n:** `(rendimiento_2027 / media_reciente - 1) ? 100`. Sin proyecci?n o con base cero se muestra ausencia de comparaci?n.
- **At?picos:** aviso descriptivo cuando el ?ltimo rendimiento difiere m?s del 30% de esa media. Es una heur?stica visual, no una prueba estad?stica. La media incluye el ?ltimo a?o y reduce, pero no elimina, su influencia.
- **Scores:** el original est? entre 0,3491 y 20,1305, no entre 0 y 1. Se conserva como `score_raw` y se deriva `score=(original-m?nimo_del_cultivo)/(m?ximo_del_cultivo-m?nimo_del_cultivo)`. Si todos los valores de un cultivo son iguales se asigna 1. Los colores usan ?0,7 alto; ?0,4 medio; inferior a 0,4 bajo. Es una medida relativa dentro del cultivo, no una probabilidad ni una escala validada entre cultivos.
- **Distritos:** 12.050 significa combinaciones de cultivo, departamento y distrito. No se presenta como n?mero de distritos geogr?ficos ?nicos; no se suministraron c?digos UBIGEO.
- **Modelo:** XGBoost es el modelo declarado en el brief. No se simulan resultados de evaluaci?n. La predicci?n 2026 se conserva en el explorador; la visualizaci?n principal conecta el ?ltimo dato real con 2027.
- **Exportaci?n:** CSV de la p?gina visible, con score normalizado y original en rankings. Incluye encabezados; no implica descargar todo el conjunto.

## API

Todos los endpoints `/api/*` requieren sesi?n.

| M?todo y ruta | Funci?n |
| --- | --- |
| `GET /health` | Comprobaci?n de conexi?n SQL |
| `POST /auth/register` | Crear cuenta; contrase?a de 10?128 caracteres |
| `POST /auth/login` | Iniciar sesi?n |
| `GET /auth/me` | Usuario actual |
| `POST /auth/logout` | Eliminar cookie |
| `GET /auth/google` | Iniciar consentimiento de Google |
| `GET /auth/google/callback` | Canjear c?digo y crear sesi?n |
| `GET /api/metadata?crop=PAPA` | Cultivos y departamentos compatibles |
| `GET /api/overview?crop=PAPA&department=` | Historial, predicciones, media y variaci?n |
| `GET /api/rankings?crop=PAPA&page=1&size=10` | Distritos ordenados por score |
| `GET /api/observations?crop=PAPA&page=1&size=20` | Explorador paginado |

`department` vac?o significa ?mbito nacional. La paginaci?n empieza en 1 y `size` acepta 1?100. Los accesos SQL usan par?metros de SQLAlchemy. Las sesiones duran ocho horas y se guardan en cookies HttpOnly con SameSite=Lax; las contrase?as nunca se devuelven por la API.

## Verificaci?n

```powershell
Set-Location backend
& .venv/Scripts/python.exe -m pytest -q
Set-Location ../frontend
npm run typecheck
npm run test:charts
npm run build
```

Las pruebas usan la base local migrada e importada. Crean usuarios temporales y los eliminan al finalizar. Verifican protecci?n de rutas, rechazo OAuth sin estado v?lido, registro duplicado, contrase?a incorrecta, cierre de sesi?n, departamentos permitidos, paginaci?n, l?mites de tama?o, media real de cinco a?os y conteos/rango de scores.

## Estructura

```text
backend/
  app/               API, modelos SQL, configuraci?n e importador
  alembic/           Migraci?n inicial y entorno Alembic
  tests/             Pruebas de integraci?n PostgreSQL
  .env.example       Configuraci?n p?blica de ejemplo
frontend/
  app/               Layout, dashboard y estilos adaptables
  components/ui/     Componentes reutilizables
  public/logo.png    Logo proporcionado
scripts/start.ps1    Arranque local en Windows
*.json               Fuentes originales
```

## L?mites del entorno local

Esta entrega est? dise?ada para uso local y no se ha desplegado. Antes de exponerla p?blicamente hacen falta HTTPS con cookies Secure, l?mites de intentos de autenticaci?n, recuperaci?n y verificaci?n de correo, gesti?n de secretos y copias de seguridad. No incluye recuperaci?n de contrase?a ni administraci?n de usuarios. La vista conserva el contexto mientras se cambia de secci?n; las secciones usan navegaci?n interna en el dashboard.

El hist?rico contiene 2026 y las predicciones tambi?n incluyen 2026; se mantienen como series distintas. No se inventan intervalos de confianza, m?tricas del modelo, datos clim?ticos ni conexiones a fuentes externas.

### Regresión de gráficos

`npm run test:charts` renderiza el componente real del dashboard con los datos de PAPA en HUANUCO. Comprueba las curvas histórica y proyectada, el área de producción, las barras y la etiqueta 2027. Las series deben ser hijos directos de `ComposedChart`: Recharts 2 no reconoce las series anidadas en fragmentos de React.

## Diseño de la interfaz

La entrada pública incluye portada fotográfica, presentación de funcionalidades y acceso al registro y al inicio de sesión. Las sesiones activas entran directamente al dashboard. Se conservan el logo, verde bosque y verde lima originales. El dashboard incluye tarjetas de proyección, una tendencia calculada del historial, acceso a rankings y un panel lateral de proyección. Los anillos son decorativos y no representan probabilidades ni precisión del modelo.

Los componentes están en `frontend/components/welcome.tsx` y `overview-highlights.tsx`, con estilos en `frontend/app/redesign.css`. Los recursos se sirven localmente desde `frontend/public/images`: fotografía de paisaje agrícola procedente de [Unsplash](https://images.unsplash.com/photo-1500382017468-9049fed747ef) e ilustración vectorial creada para AgroData. La foto es ilustrativa y no se identifica como una ubicación geográfica peruana.

## Modelo freemium: avance por pasos

Paso 1: landing pública en `/`, identidad centrada, gradiente verde, CTA hacia `/resumen` y tarjetas de cobertura, modelo y cultivos. Se verificaron 1.790 pares departamento/distrito y 20 cultivos; R²=0,98 se identifica como declarado en el brief, sin equipararlo a porcentaje de precisión. La ruta `/resumen` conserva temporalmente la autenticación existente. Abrir el dashboard básico, crear el soft gate e integrar Clerk quedan pendientes de las confirmaciones solicitadas por el brief. No se han cambiado la base PostgreSQL ni sus permisos en este paso.

## AgroBot: API conversacional (fase 1)

API implementada: `frontend/app/api/chat/route.ts`, `frontend/lib/chat-handler.ts` y `frontend/lib/chat-context.ts`. Utiliza Vercel AI SDK con un proveedor configurable: DeepSeek u OpenAI. La API se implementó y validó antes del widget. La interfaz se añadió posteriormente tras la confirmación del usuario.

### Configuración

Copia `frontend/.env.local.example` a `frontend/.env.local` y configura:

```dotenv
OPENAI_API_KEY=tu_clave_privada
OPENAI_MODEL=identificador_de_un_modelo_de_tu_cuenta
```

El modelo debe admitir Chat Completions. Las variables son exclusivamente del servidor, nunca `NEXT_PUBLIC_*`. Reinicia Next.js tras cambiarlas. Una cuenta de ChatGPT o la conexión de Drive no configura esta clave de API. No pegues secretos en el chat ni los subas al repositorio.

La app permanece local, pero cada consulta habilitada enviará al proveedor externo las preguntas de la conversación y el resumen agrícola seleccionado; requiere Internet y puede consumir crédito de API. No se ha hecho una llamada real de pago en esta entrega.

### Fuentes y contexto

El lector busca primero cada JSON en `frontend/public/`, luego en `frontend/public/dashboard_data/` y finalmente en la raíz del proyecto. Reutiliza los originales existentes y no publica copias completas. Lee historial y predicciones nacionales/departamentales, scoring y, si existe, `metadata.json`. En ausencia de metadatos, deriva cultivos, períodos y conteos de los datos. Los archivos deben permanecer disponibles al ejecutar Next.js; el trace de `/api/chat` incluye los originales para su empaquetado.

El resumen incluye top 5 por cultivo, hasta 20 coincidencias de distritos mencionados, series nacionales, series regionales cuando se reconoce un departamento y comparaciones de cinco años calculadas en código. El histórico y las predicciones mantienen sus unidades originales. Los rankings se ordenan por score original, diferenciándolo del rendimiento. El score relativo sigue la normalización por cultivo del dashboard. Los archivos se cargan una vez por proceso; tras modificarlos hay que reiniciar Next.js para actualizar el contexto.

R²=0,9839, WMAPE=7,03% y 1.668 distritos se identifican como declaraciones del nuevo brief. No hay informe de evaluación adjunto. El conteo derivado sigue siendo 1.790 pares departamento/distrito y 12.050 registros distrito/cultivo. R² no se convierte en porcentaje de precisión.

Las instrucciones limitan AgroBot a los datos disponibles, piden reconocer la falta de información y citar los nombres de las fuentes. Inyectar contexto no garantiza ausencia de errores; las respuestas generadas deben contrastarse con el dashboard cuando se requiera exactitud.

### Contrato HTTP

`POST /api/chat`, `Content-Type: application/json`:

```json
{"messages":[{"role":"user","content":"¿Cuál es el mejor distrito para PAPA?"}]}
```

También acepta mensajes de texto del AI SDK mediante `parts: [{"type":"text","text":"..."}]`. Solo admite roles `user` y `assistant`, y el último mensaje debe ser del usuario. El sistema no acepta instrucciones de sistema suministradas por el cliente.

La respuesta correcta es **SSE del protocolo UI Message del AI SDK**, preparada para el futuro widget con `useChat`/`DefaultChatTransport`. Los eventos incluyen `text-start`, `text-delta`, `text-end` y finalización. No es una respuesta JSON ni texto plano. Un fallo del proveedor después de iniciar el stream produce un evento de error legible, sin detalles internos.

| Estado | Significado |
| --- | --- |
| 400 | Mensajes o JSON inválidos |
| 403 | Origin ajeno a AgroData |
| 413 | Cuerpo o conversación demasiado largos |
| 415 | Falta Content-Type JSON |
| 422 | Contexto demasiado amplio; especificar cultivo/departamento |
| 429 | Límite temporal de llamadas alcanzado |
| 503 | Falta clave/modelo o no se pudieron cargar las fuentes |
| 502 | Fallo previo al inicio del streaming del proveedor |

Límites locales: cuerpo de 32 KiB, 12 mensajes, 4.000 caracteres por mensaje, 16.000 en total, contexto de 120.000 caracteres, salida de 900 tokens y timeout de 60 segundos. Hay un límite global de 20 consultas por minuto **por proceso**; no es un control distribuido. El endpoint es público para la demostración local. Antes de exponerlo externamente hacen falta cuotas persistentes por usuario/cliente y control de gasto.

### Pruebas

```powershell
cd frontend
npm run test:chat
npm run typecheck
```

Nueve pruebas sin llamadas externas verifican el ranking real de PAPA, contexto de Huánuco con tildes, proyección 2027, base de cinco años, metadatos derivados/declarados, formato SSE, texto por `parts`, rechazo de mensajes inválidos, redacción de errores y límite temporal. Utilizan el modelo simulado oficial del AI SDK; no acreditan la calidad de respuestas de un modelo real ni validan credenciales.

Referencias: [streamText del AI SDK](https://ai-sdk.dev/docs/reference/ai-sdk-core/stream-text) y [autenticación de la API de OpenAI](https://developers.openai.com/api/reference/overview).

### Tipografía editorial

Los títulos principales de la portada y del dashboard usan Old Standard TT (regular y cursiva), servida localmente desde `frontend/public/fonts/old-standard-tt/`. La licencia OFL se conserva en esa carpeta. La cursiva se aplica a la frase destacada «Predicción Agrícola». Menús, tablas y texto de lectura mantienen la tipografía de interfaz existente.

## AgroBot: widget conversacional

El bot aparece en todas las páginas como un botón flotante verde en la esquina inferior derecha. Al abrirlo muestra tres sugerencias, mensajes de usuario y asistente, y un campo para preguntar. Consume `/api/chat` mediante `useChat` y `DefaultChatTransport` del Vercel AI SDK. Renderiza Markdown sin ejecutar HTML, imágenes ni enlaces generados por el modelo.

Incluye indicador de consulta/respuesta, detención de la generación, nueva conversación, reintento ante errores y cierre con Escape devolviendo el foco al botón. Conserva el chat en memoria al navegar entre páginas y al cerrar la ventana; no persiste mensajes en disco. Limita el historial enviado a los once mensajes recientes dentro del presupuesto de 16.000 caracteres. Cada pregunta admite hasta 2.000 caracteres.

Si falta la configuración del proveedor, el widget lo indica sin inventar una respuesta. Configura `OPENAI_API_KEY` y `OPENAI_MODEL` en `frontend/.env.local`, y reinicia Next.js. El indicador del botón identifica el asistente; no es una comprobación de disponibilidad del proveedor. Los componentes están en `frontend/components/chat/` y los estilos en `frontend/app/chat.css`.

La verificación del widget en Chrome cubrió sugerencias, Markdown por streaming, historial de seguimiento, nueva conversación, errores de configuración y reintento, indicador de carga/detención, ancho móvil y retorno del foco con Escape. Las solicitudes de IA se interceptaron con respuestas de prueba, sin llamadas de pago.

### Proveedor DeepSeek

La configuración actual usa DeepSeek mediante su API compatible con Chat Completions. En `frontend/.env.local`:

```dotenv
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=tu_clave_de_deepseek
DEEPSEEK_MODEL=deepseek-flash
```

El proveedor se selecciona en `frontend/lib/chat-provider.ts`. Las solicitudes de DeepSeek van exclusivamente a `https://api.deepseek.com/v1`; su clave no se envía a OpenAI. No pegues una clave en el campo del modelo. La configuración rechaza nombres de modelo que comiencen con `sk-`. El archivo `.env.local` está ignorado por Git. Reinicia Next.js después de cambiarlo.

Para usar OpenAI como alternativa configura `AI_PROVIDER=openai`, `OPENAI_API_KEY` y `OPENAI_MODEL`; una clave de un proveedor no sirve para autenticarte con el otro. Las preguntas y su contexto se envían al proveedor seleccionado.

Referencia: [Primera llamada a la API de DeepSeek](https://api-docs.deepseek.com/). La selección del proveedor, del endpoint y de su clave se comprueba en las pruebas de chat.

### Inicio del backend desde CMD

Desde la raíz puedes ejecutar `scripts\start-backend.cmd`. También puedes entrar a `backend` y ejecutar `.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. La terminal debe permanecer abierta; Ctrl+C detiene la API. PostgreSQL debe estar activo en el puerto configurado. Si el puerto 8000 ya está ocupado, comprueba `http://localhost:8000/docs` antes de lanzar otra instancia.

El Home incluye fondo fotográfico local y secciones de presentación del proyecto: Quiénes somos y Nosotros, con enlaces visibles en escritorio y móvil. No se publican datos personales no proporcionados.

Si los JSON originales ya no están disponibles, el contexto de AgroBot obtiene una instantánea de solo lectura desde PostgreSQL mediante `backend/app/chat_snapshot.py` y el Python local del proyecto. No vuelve a crear archivos eliminados. La instantánea permanece en memoria hasta reiniciar Next.js. Esta alternativa requiere mantener la carpeta backend y su entorno virtual junto al frontend; no es un despliegue autónomo de Next.js.
