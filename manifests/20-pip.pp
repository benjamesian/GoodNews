# Install pip and related Python packages

package {'python3-pip':
  ensure  => installed,
}

exec {'pip-upgrade':
  command => 'python3 -m pip install --upgrade pip',
  path    => '/usr/bin:/bin',
  require => Package['python3-pip'],
}

exec {'pip-requirements':
  command => 'python3 -m pip install -U -r /data/current/requirements.txt',
  path    => '/usr/bin:/bin',
  require => Exec['pip-upgrade'],
}
