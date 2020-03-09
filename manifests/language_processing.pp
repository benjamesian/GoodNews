# Set up the language processing service on a server

service {'language_processing.service':
  ensure    => running,
  enable    => true,
  provider  => systemd,
  require   => File['language_processing.service'],
  subscribe => Exec['daemon-reload'],
}

file {'language_processing.service':
  ensure  => file,
  path    => '/etc/systemd/system/language_processing.service',
  source  => '/data/current/etc/systemd/system/language_processing.service',
  mode    => '0644',
  owner   => 'root',
  group   => 'root',
  require => Exec['stop'],
  notify  => Exec['daemon-reload'],
}

exec {'stop':
  command => 'systemctl stop language_processing',
  path    => '/usr/bin:/bin',
}

exec {'daemon-reload':
  command     => 'systemctl daemon-reload',
  path        => '/usr/bin:/bin',
  refreshonly => true,
}
