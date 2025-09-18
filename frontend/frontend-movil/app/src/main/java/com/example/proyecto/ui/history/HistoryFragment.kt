package com.example.proyecto.ui.history

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Toast
import androidx.fragment.app.Fragment
import androidx.fragment.app.viewModels
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.example.proyecto.R
import com.example.proyecto.data.repo.HeartRepo
import kotlinx.coroutines.flow.collectLatest

class HistoryFragment : Fragment() {
    private val vm: HistoryViewModel by viewModels {
        object : ViewModelProvider.Factory {
            override fun <T : ViewModel> create(modelClass: Class<T>): T {
                return HistoryViewModel(HeartRepo(requireContext())) as T
            }
        }
    }

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View? {
        val view = inflater.inflate(R.layout.fragment_history, container, false)
        // El ID correcto es 'rvVitals' según tu archivo de layout.
        val rv = view.findViewById<RecyclerView>(R.id.rvVitals) // <-- LÍNEA CORREGIDA
        val adapter = VitalAdapter()

        rv.adapter = adapter
        rv.layoutManager = LinearLayoutManager(context)

        viewLifecycleOwner.lifecycleScope.launchWhenStarted {
            vm.vitals.collectLatest { vitals ->
                adapter.submitList(vitals)
            }
        }

        viewLifecycleOwner.lifecycleScope.launchWhenStarted {
            vm.error.collectLatest { error ->
                error?.let {
                    Toast.makeText(context, it, Toast.LENGTH_SHORT).show()
                }
            }
        }

        return view
    }

    override fun onResume() {
        super.onResume()
        vm.load()
    }
}