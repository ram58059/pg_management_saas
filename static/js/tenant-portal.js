(function () {
  'use strict';

  const sidebar = document.getElementById('tenant-sidebar');
  const backdrop = document.getElementById('tenant-sidebar-backdrop');
  const openButton = document.getElementById('tenant-sidebar-open');

  function openSidebar() {
    if (!sidebar || !backdrop) return;
    sidebar.classList.add('is-open');
    backdrop.classList.remove('hidden');
    backdrop.classList.add('is-open');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    if (!sidebar || !backdrop) return;
    sidebar.classList.remove('is-open');
    backdrop.classList.add('hidden');
    backdrop.classList.remove('is-open');
    document.body.style.overflow = '';
  }

  openButton?.addEventListener('click', openSidebar);
  backdrop?.addEventListener('click', closeSidebar);

  sidebar?.querySelectorAll('.owner-nav-link').forEach((link) => {
    link.addEventListener('click', () => {
      if (window.innerWidth < 1024) {
        closeSidebar();
      }
    });
  });

  window.addEventListener('resize', () => {
    if (window.innerWidth >= 1024) {
      closeSidebar();
    }
  });

  window.StayiPortal = window.StayiPortal || {};
  window.StayiPortal.openModal = function (modal) {
    if (!modal) return;
    if (modal.parentElement !== document.body) {
      document.body.appendChild(modal);
    }
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  };

  window.StayiPortal.closeModal = function (modal) {
    if (!modal) return;
    modal.classList.add('hidden');
    document.body.style.overflow = '';
  };
})();
