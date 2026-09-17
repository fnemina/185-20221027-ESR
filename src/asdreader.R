# ==============================================================================
# asdreader.R: Módulo en R para lectura, calibración y procesamiento bio-óptico
# de mediciones de espectrorradiómetros ASD FieldSpec (v8)
# Proyecto: 185-20221027-ESR (PROSAT II-ARG)
# ==============================================================================

# Definición de formatos de datos ASD
ASD_DATA_FORMAT <- c("0" = "FLOAT_FORMAT", "1" = "INTEGER_FORMAT", 
                     "2" = "DOUBLE_FORMAT", "3" = "UNKNOWN_FORMAT")

#' Leer un archivo espectrorradiométrico binario de ASD (.asd / .ref / .ill / .raw)
#'
#' @param path Ruta al archivo binario .asd
#' @param name Nombre identificador del espectro (opcional)
#' @return Objeto de clase 'Spectra' con campos: name, wave, spectrum, metadata
readASD <- function(path, name = "") {
  if (!file.exists(path)) {
    stop(paste("Archivo no encontrado:", path))
  }
  
  con <- file(path, "rb")
  on.exit(close(con))
  
  # 1. Leer cabecera binaria de 484 bytes
  header_raw <- readBin(con, what = "raw", n = 484)
  if (length(header_raw) < 484) {
    stop("El archivo es demasiado corto para contener una cabecera ASD v8 válida.")
  }
  
  # Versión del producto (primeros 3 bytes)
  product_version <- rawToChar(header_raw[1:3])
  
  # Comentarios (157 bytes a partir del byte 4)
  comments_raw <- header_raw[4:160]
  comments_raw <- comments_raw[comments_raw != as.raw(0)]
  comments <- if (length(comments_raw) > 0) rawToChar(comments_raw) else ""
  
  # Fecha y hora (9 enteros con signo de 16 bits en little-endian desde offset 160)
  date_vals <- readBin(header_raw[161:178], what = "integer", n = 9, size = 2, signed = TRUE, endian = "little")
  second <- date_vals[1]
  minute <- date_vals[2]
  hour   <- date_vals[3]
  day    <- date_vals[4]
  month  <- date_vals[5] + 1
  year   <- date_vals[6] + 1900
  measurement_date <- sprintf("%04d-%02d-%02d %02d:%02d:%02d", year, month, day, hour, minute, second)
  
  # Canales y parámetros de longitud de onda (desde offset 191)
  ch1_wave  <- readBin(header_raw[192:195], what = "numeric", n = 1, size = 4, endian = "little")
  wave_step <- readBin(header_raw[196:199], what = "numeric", n = 1, size = 4, endian = "little")
  
  # Formato de datos (byte en offset 199, índice 200 en R)
  data_format_byte <- as.integer(header_raw[200])
  data_format <- ASD_DATA_FORMAT[as.character(data_format_byte)]
  if (is.na(data_format)) data_format <- "UNKNOWN_FORMAT"
  
  # Número de canales espectrales (offset 204, 2 bytes sin signo)
  channels <- readBin(header_raw[205:206], what = "integer", n = 1, size = 2, signed = FALSE, endian = "little")
  
  # Tiempo de integración (offset 390, 4 bytes)
  integration_time_val <- readBin(header_raw[391:394], what = "integer", n = 1, size = 4, endian = "little")
  integration_time <- if (integration_time_val == 8) 8.5 else as.numeric(integration_time_val)
  
  # Ganancias y offsets de detectores SWIR1 y SWIR2 (offset 436, cuatro enteros sin signo de 2 bytes)
  swir_vals <- readBin(header_raw[437:444], what = "integer", n = 4, size = 2, signed = FALSE, endian = "little")
  swir1_gain   <- swir_vals[1]
  swir2_gain   <- swir_vals[2]
  swir1_offset <- swir_vals[3]
  swir2_offset <- swir_vals[4]
  
  # Longitudes de onda de empalme instrumental (Splices) (offset 444, dos floats de 4 bytes)
  splice_vals <- readBin(header_raw[445:452], what = "numeric", n = 2, size = 4, endian = "little")
  splice1_wavelength <- splice_vals[1]
  splice2_wavelength <- splice_vals[2]
  
  metadata <- list(
    product_version = product_version,
    comments = comments,
    measurement_date = measurement_date,
    ch1_wave = ch1_wave,
    wave_step = wave_step,
    data_format = data_format,
    channels = channels,
    integration_time = integration_time,
    swir1_gain = swir1_gain,
    swir2_gain = swir2_gain,
    swir1_offset = swir1_offset,
    swir2_offset = swir2_offset,
    splice1_wavelength = splice1_wavelength,
    splice2_wavelength = splice2_wavelength
  )
  
  # 2. Leer datos espectrales a partir del byte 484
  seek(con, where = 484, origin = "start")
  
  if (data_format == "DOUBLE_FORMAT") {
    spectrum <- readBin(con, what = "double", n = channels, size = 8, endian = "little")
  } else if (data_format == "FLOAT_FORMAT") {
    spectrum <- readBin(con, what = "numeric", n = channels, size = 4, endian = "little")
  } else {
    stop(paste("Formato de datos no soportado:", data_format))
  }
  
  wave <- seq(from = ch1_wave, by = wave_step, length.out = channels)
  
  res <- list(
    name = if (name == "") basename(path) else name,
    wave = wave,
    spectrum = spectrum,
    metadata = metadata
  )
  class(res) <- c("Spectra", "list")
  return(res)
}

#' Calibración radiométrica absoluta de cuentas digitales a radiancia espectral
#'
#' @param DN Objeto Spectra con cuentas crudas de campo
#' @param ref Objeto Spectra con reflectancia del panel de laboratorio
#' @param ill Objeto Spectra con irradiancia de la lámpara patrón de laboratorio
#' @param raw Objeto Spectra con cuentas crudas de calibración en laboratorio
#' @return Objeto Spectra con radiancia espectral calibrada L [W m^-2 nm^-1 sr^-1]
calibrateASD <- function(DN, ref, ill, raw) {
  channels <- DN$metadata$channels
  
  # Factores de ganancia instrumental de campo (IG)
  IG <- rep(2048 / DN$metadata$swir1_gain, channels)
  IG[DN$wave > DN$metadata$splice2_wavelength]  <- 2048 / DN$metadata$swir2_gain
  IG[DN$wave <= DN$metadata$splice1_wavelength] <- DN$metadata$integration_time
  
  # Factores de ganancia instrumental de laboratorio (IGr)
  IGr <- rep(2048 / raw$metadata$swir1_gain, raw$metadata$channels)
  IGr[raw$wave > raw$metadata$splice2_wavelength]  <- 2048 / raw$metadata$swir2_gain
  IGr[raw$wave <= raw$metadata$splice1_wavelength] <- raw$metadata$integration_time
  
  # Ecuación de calibración radiométrica absoluta (NIST)
  L_spectrum <- (ref$spectrum * ill$spectrum * DN$spectrum) / (pi * raw$spectrum) * (IGr / IG)
  
  res <- list(
    name = paste0("L_", DN$name),
    wave = DN$wave,
    spectrum = L_spectrum,
    metadata = DN$metadata
  )
  class(res) <- c("Spectra", "list")
  return(res)
}

#' Corrección parabólica continua de discontinuidades de empalme (Splice Correction)
#'
#' @param L Objeto Spectra de radiancia calibrada
#' @param xv1 Longitud de onda límite de anclaje para Splice 1 (por defecto 675 nm)
#' @param xv2 Longitud de onda límite de anclaje para Splice 2 (por defecto 1975 nm)
#' @return Objeto Spectra de radiancia corregida
parabolicASD <- function(L, xv1 = 675, xv2 = 1975) {
  x <- L$wave
  
  # Empalme 1: VNIR a SWIR1 (aprox. 1000 nm)
  xO1 <- L$metadata$splice1_wavelength + 1
  xU1 <- L$metadata$splice1_wavelength
  yO1 <- L$spectrum[which(L$wave == xO1)[1]]
  yU1 <- L$spectrum[which(L$wave == xU1)[1]]
  
  yp1 <- (x - xv1)^2 / (xO1 - xv1)^2 * (yO1 - yU1) / yU1 + 1
  yp1[L$wave < xv1] <- 1
  yp1[L$wave > L$metadata$splice1_wavelength] <- 1
  
  # Empalme 2: SWIR1 a SWIR2 (aprox. 1800 nm)
  xO2 <- L$metadata$splice2_wavelength + 1
  xU2 <- L$metadata$splice2_wavelength - 1
  yO2 <- L$spectrum[which(L$wave == xO2)[1]]
  yU2 <- L$spectrum[which(L$wave == xU2)[1]]
  
  yp2 <- (x - xv2)^2 / (xO2 - xv2)^2 * (yU2 - yO2) / yO2 + 1
  yp2[L$wave > xv2] <- 1
  yp2[L$wave <= L$metadata$splice2_wavelength] <- 1
  
  Lp_spectrum <- L$spectrum * (yp1 * yp2)
  
  res <- list(
    name = paste0("Lp_", L$name),
    wave = L$wave,
    spectrum = Lp_spectrum,
    metadata = L$metadata
  )
  class(res) <- c("Spectra", "list")
  return(res)
}

#' Factor de reflectancia de Fresnel según velocidad del viento (Mobley, 1999)
#'
#' @param wind Velocidad del viento en m/s
#' @return Factor de reflexión superficial rho_F (adimensional)
getRhoF <- function(wind) {
  if (wind >= 999 || is.na(wind) || wind < 0) wind <- 0
  0.0256 + 0.00039 * wind + 0.000034 * (wind^2)
}

#' Procesamiento de estación radiométrica de agua (WaterSample)
#' Calcula reflectancia de teledetección (Rrs) y propagación de incertidumbre
#'
#' @param ref_list Lista de objetos Spectra para panel Spectralon (spc)
#' @param wat_list Lista de objetos Spectra para agua emergente (wat)
#' @param sky_list Lista de objetos Spectra para cielo difuso (sky)
#' @param wind Velocidad del viento en m/s
#' @param maxwl Longitud de onda máxima de corte (por defecto 850 nm)
#' @return Lista con data.frame de resultados espectrales y metadatos
calcWaterSample <- function(ref_list, wat_list, sky_list, wind, maxwl = 850) {
  # Matrices de espectros (filas = espectros/réplicas, columnas = longitudes de onda)
  mat_ref <- do.call(rbind, lapply(ref_list, function(s) s$spectrum))
  mat_wat <- do.call(rbind, lapply(wat_list, function(s) s$spectrum))
  mat_sky <- do.call(rbind, lapply(sky_list, function(s) s$spectrum))
  
  # Promedios espectrales
  mr <- colMeans(mat_ref, na.rm = TRUE)
  mw <- colMeans(mat_wat, na.rm = TRUE)
  ms <- colMeans(mat_sky, na.rm = TRUE)
  
  # Desviaciones estándar espectrales entre réplicas
  # Si solo hay 1 réplica, sd da NA; reemplazamos por 0
  sdr <- apply(mat_ref, 2, sd)
  sdw <- apply(mat_wat, 2, sd)
  sds <- apply(mat_sky, 2, sd)
  sdr[is.na(sdr)] <- 0
  sdw[is.na(sdw)] <- 0
  sds[is.na(sds)] <- 0
  
  # Irradiancia descendente Ed = pi * L_spc
  Ed <- mr * pi
  
  # Coeficiente de Fresnel y Reflectancia Rrs
  rhoF <- getRhoF(wind)
  Rrs <- (mw - rhoF * ms) / Ed
  
  # Propagación analítica de incertidumbre (uRrs)
  uRrs <- sqrt(((1 / Ed) * sdw)^2 + 
               ((rhoF / Ed) * sds)^2 + 
               ((((mw - rhoF * ms) / (Ed^2)) * sdr)^2))
  
  # Incertidumbre relativa porcentual (%)
  rRrs <- 100 * (uRrs / Rrs)
  
  wave <- ref_list[[1]]$wave
  
  # Filtrar por longitud de onda máxima
  idx <- which(wave <= maxwl)
  
  df <- data.frame(
    wave = wave[idx],
    L_spc = mr[idx],
    L_wat = mw[idx],
    L_sky = ms[idx],
    Ed = Ed[idx],
    Rrs = Rrs[idx],
    uRrs = uRrs[idx],
    rRrs = rRrs[idx]
  )
  
  return(list(
    data = df,
    wind = wind,
    rhoF = rhoF,
    n_ref = length(ref_list),
    n_wat = length(wat_list),
    n_sky = length(sky_list)
  ))
}

#' Integración trapezoidal numérica
#'
#' @param x Vector de coordenadas independientes (longitud de onda)
#' @param y Vector de valores a integrar
#' @return Valor numérico de la integral
trapz <- function(x, y) {
  if (length(x) != length(y)) stop("x e y deben tener la misma longitud")
  idx <- order(x)
  x <- x[idx]
  y <- y[idx]
  n <- length(x)
  if (n < 2)  return(0)
  sum(diff(x) * (y[-1] + y[-n]) / 2)
}

#' Método print para clase Spectra
print.Spectra <- function(x, ...) {
  cat("<Spectra:", x$name, ">\n")
  cat(" Canales:", length(x$wave), "\n")
  cat(" Rango espectral:", min(x$wave), "-", max(x$wave), "nm\n")
  if (!is.null(x$metadata)) {
    cat(" Fecha adquisición:", x$metadata$measurement_date, "\n")
    cat(" Formato:", x$metadata$data_format, "\n")
    cat(" Tiempo integración:", x$metadata$integration_time, "\n")
  }
  invisible(x)
}

#' Método plot para clase Spectra
plot.Spectra <- function(x, y, ..., xlab = "Longitud de onda [nm]", ylab = "Respuesta", type = "l", col = "steelblue", lwd = 1.5) {
  plot(x$wave, x$spectrum, type = type, xlab = xlab, ylab = ylab, col = col, lwd = lwd, ...)
  grid(col = "gray80", lty = "dotted")
}

#' Leer tabla de Funciones de Respuesta Espectral Relativa (RSR)
#' Compatible de forma transparente con archivos .csv y .nc
#'
#' @param path Ruta al archivo .csv o .nc con las curvas RSR
#' @return data.frame con columnas: wavelength y las bandas satelitales
readRSR <- function(path) {
  # Si el archivo indicado es .nc pero no existe o ncdf4 no está instalado, buscar .csv
  if (grepl("[.]nc$", path, ignore.case = TRUE)) {
    csv_path <- sub("[.]nc$", ".csv", path, ignore.case = TRUE)
    if (file.exists(csv_path)) {
      return(read.csv(csv_path))
    }
    if (requireNamespace("ncdf4", quietly = TRUE)) {
      nc <- ncdf4::nc_open(path)
      on.exit(ncdf4::nc_close(nc))
      bands <- ncdf4::ncvar_get(nc, "bands")
      wl <- ncdf4::ncvar_get(nc, "wavelength")
      rsr_mat <- ncdf4::ncvar_get(nc, "RSR") # dimensiones: bands x wavelengths
      df <- as.data.frame(t(rsr_mat))
      colnames(df) <- paste0("O_", as.integer(bands))
      df$wavelength <- as.numeric(wl)
      df <- df[, c("wavelength", setdiff(names(df), "wavelength"))]
      return(df)
    } else {
      stop(paste("Paquete ncdf4 no instalado y no se encontró archivo CSV equivalente:", csv_path))
    }
  } else {
    return(read.csv(path))
  }
}

