package com.tomoko.fyntra.ui.components

import androidx.compose.foundation.Image
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ExitToApp
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.unit.dp
import com.tomoko.fyntra.R

@Composable
fun AppHeader(
    onLogout: () -> Unit,
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .fillMaxWidth()
            .padding(16.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Image(
            painter = painterResource(id = R.drawable.imagotipo),
            contentDescription = "Fyntra Logo",
            modifier = Modifier.size(120.dp)
        )
        
        IconButton(
            onClick = onLogout
        ) {
            Icon(
                imageVector = Icons.Filled.ExitToApp,
                contentDescription = "Cerrar sesión",
                tint = Color(0xFF1B9D8A),
                modifier = Modifier.size(24.dp)
            )
        }
    }
}
