package com.example.proyecto.ui.login

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.lifecycleScope
import androidx.navigation.fragment.findNavController
import com.example.proyecto.R
import com.example.proyecto.data.repo.HeartRepo
import com.example.proyecto.ui.login.LoginViewModel // <-- AÑADE ESTA LÍNEA
import kotlinx.coroutines.flow.collectLatest

class LoginFragment : Fragment() {
    private val vm: LoginViewModel by viewModels {
        object : ViewModelProvider.Factory {
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                return LoginViewModel(HeartRepo(requireContext())) as T
            }
        }
    }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        val v = inflater.inflate(R.layout.fragment_login, container, false)
        val email = v.findViewById<EditText>(R.id.email)
        val pass = v.findViewById<EditText>(R.id.password)
        v.findViewById<View>(R.id.btnLogin).setOnClickListener {
            vm.login(email.text.toString(), pass.text.toString())
        }
        return v
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        viewLifecycleOwner.lifecycleScope.launchWhenStarted {
            vm.state.collectLatest { st ->
                when (st) {
                    is LoginState.Success -> findNavController().navigate(R.id.action_login_to_dashboard)
                    is LoginState.Error -> Toast.makeText(requireContext(), st.msg, Toast.LENGTH_SHORT).show()
                    else -> Unit
                }
            }
        }
    }
}