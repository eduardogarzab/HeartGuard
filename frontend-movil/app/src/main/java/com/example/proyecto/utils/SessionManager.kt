package com.example.proyecto.utils

// Android/app/src/main/java/com/heartguard/utils/SessionManager.kt

import android.content.Context
import android.content.SharedPreferences

class SessionManager(ctx: Context) {
    private val prefs: SharedPreferences = ctx.getSharedPreferences("hg_prefs", Context.MODE_PRIVATE)
    fun saveToken(token: String) = prefs.edit().putString("jwt", token).apply()
    fun getToken(): String? = prefs.getString("jwt", null)
    fun clear() = prefs.edit().clear().apply()
}
