function showPermissionsModal(userId) {
  const modal = document.getElementById('permissionsModal_' + userId);
  if (modal) {
    const modalInstance = new bootstrap.Modal(modal);
    modalInstance.show();
  }
}
