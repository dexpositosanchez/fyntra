-- Migración para crear usuarios para todos los conductores que no tienen usuario
-- Fecha: 2026-01-27
-- Descripción: Crea usuarios para todos los conductores que tienen email pero no tienen usuario_id

-- Crear usuarios para conductores sin usuario pero con email
DO $$
DECLARE
    conductor_record RECORD;
    nuevo_usuario_id INTEGER;
    nombre_completo TEXT;
    password_default TEXT;
BEGIN
    FOR conductor_record IN 
        SELECT id, nombre, apellidos, email, activo
        FROM conductores
        WHERE usuario_id IS NULL AND email IS NOT NULL
    LOOP
        -- Construir nombre completo
        nombre_completo := conductor_record.nombre;
        IF conductor_record.apellidos IS NOT NULL THEN
            nombre_completo := nombre_completo || ' ' || conductor_record.apellidos;
        END IF;
        
        -- Generar password por defecto (parte antes del @ del email + "123")
        password_default := split_part(conductor_record.email, '@', 1) || '123';
        
        -- Verificar que no exista ya un usuario con ese email
        IF NOT EXISTS (SELECT 1 FROM usuarios WHERE email = conductor_record.email) THEN
            -- Crear usuario
            INSERT INTO usuarios (nombre, email, hash_password, rol, activo, creado_en)
            VALUES (
                nombre_completo,
                conductor_record.email,
                crypt(password_default, gen_salt('bf')),  -- Usar bcrypt (requiere extensión pgcrypto)
                'conductor',
                conductor_record.activo,
                NOW()
            )
            RETURNING id INTO nuevo_usuario_id;
            
            -- Actualizar conductor con el usuario_id
            UPDATE conductores
            SET usuario_id = nuevo_usuario_id
            WHERE id = conductor_record.id;
            
            RAISE NOTICE 'Usuario creado para conductor % (ID: %) con email %', nombre_completo, conductor_record.id, conductor_record.email;
        ELSE
            RAISE NOTICE 'Ya existe un usuario con el email % para el conductor % (ID: %)', conductor_record.email, nombre_completo, conductor_record.id;
        END IF;
    END LOOP;
END $$;

-- Si no tienes la extensión pgcrypto instalada, usa esta versión alternativa:
-- (Requiere que el backend genere el hash con Python antes de ejecutar)

-- Alternativa sin pgcrypto (requiere ejecutar desde Python):
-- Este script debe ejecutarse desde Python usando get_password_hash de app.core.security
