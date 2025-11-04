import React, { useState } from 'react';
import { X, User, CreditCard, Loader } from 'lucide-react';
import apiService from '../../services/apiService';
import './Modal.css';

const AdminLoginModal = ({ onClose, onLogin }) => {
  const [formData, setFormData] = useState({
    name: '',
    adminId: '',
    email: ''
  });
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = () => {
    const newErrors = {};
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }
    if (!formData.adminId.trim()) {
      newErrors.adminId = 'ID is required';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleConfirm = async () => {
    if (!validateForm()) return;
    
    try {
      setLoading(true);
      const response = await apiService.adminLogin({
        name: formData.name,
        admin_id: formData.adminId
      });
      
      // Store email in the response data
      response.email = formData.email;
      
      if (response.success) {
        onLogin({
          name: formData.name,
          adminId: formData.adminId,
          email: formData.email,
          isAdmin: response.is_admin,
          userId: response.user_id
        });
        onClose();
      }
    } catch (error) {
      console.error('Admin login failed:', error);
      setErrors({ api: error.message || 'Login failed. Please try again.' });
    } finally {
      setLoading(false);
    }
  };

  const handleOverlayClick = (e) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="modal-overlay" onClick={handleOverlayClick}>
      <div className="modal admin-login-modal">
        <div className="modal-header">
          <div className="modal-title-section">
            <h2 className="modal-title">Login</h2>
            <p className="modal-subtitle">Enter your credentials</p>
          </div>
          <button className="modal-close" onClick={onClose}>
            <X size={24} />
          </button>
        </div>

        <div className="modal-body">
          <div className="step-content fade-in">
            <div className="form-group">
              <label className="form-label">
                <User size={18} />
                Full Name
              </label>
              <input
                type="text"
                name="name"
                className={`input ${errors.name ? 'input-error' : ''}`}
                placeholder="Enter your full name"
                value={formData.name}
                onChange={handleInputChange}
                autoFocus
              />
              {errors.name && (
                <span className="error-text">{errors.name}</span>
              )}
            </div>

            <div className="form-group">
              <label className="form-label">
                <CreditCard size={18} />
                ID
              </label>
              <input
                type="text"
                name="adminId"
                className={`input ${errors.adminId ? 'input-error' : ''}`}
                placeholder="Enter your ID"
                value={formData.adminId}
                onChange={handleInputChange}
              />
            {errors.adminId && (
              <span className="error-text">{errors.adminId}</span>
            )}
          </div>

          <div className="form-group">
            <label className="form-label">
              Email (optional)
            </label>
            <input
              type="email"
              name="email"
              className="input"
              placeholder="your@email.com"
              value={formData.email}
              onChange={handleInputChange}
            />
          </div>

          {errors.api && (
              <div className="error-banner">
                <span className="error-text">{errors.api}</span>
              </div>
            )}
          </div>
        </div>

        <div className="modal-footer">
          <button className="btn btn-outline" onClick={onClose}>
            Cancel
          </button>
          <button 
            className="btn btn-primary" 
            onClick={handleConfirm}
            disabled={loading}
          >
            {loading ? (
              <>
                <Loader className="spinning" size={18} />
                Logging in...
              </>
            ) : (
              'Confirm'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminLoginModal;
