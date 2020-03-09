# Set up language processing on a new server

service {'language_processing':
  ensure    => running,
  enable    => true,
  provider  => systemd,
  subscribe => Exec['reload'],
}

file {'language_processing.service':
  ensure  => file,
  path    => '/etc/systemd/system/language_processing.service',
  source  => '/opt/goodnews/etc/systemd/system/language_processing.service',
  mode    => '0644',
  owner   => 'root',
  group   => 'root',
  before  => Service['language_processing'],
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
