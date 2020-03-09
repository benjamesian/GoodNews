# Set up the language processing service on a server

service {'goodnews.service':
  ensure    => running,
  enable    => true,
  provider  => systemd,
  require   => File['goodnews.service'],
  subscribe => Exec['daemon-reload'],
}

file {'goodnews.service':
  ensure  => file,
  path    => '/etc/systemd/system/goodnews.service',
  source  => '/data/current/etc/systemd/system/goodnews.service',
  mode    => '0644',
  owner   => 'root',
  group   => 'root',
  require => Exec['stop'],
  notify  => Exec['daemon-reload'],
}

exec {'stop':
  command => 'systemctl stop goodnews',
  path    => '/usr/bin:/bin',
}

exec {'daemon-reload':
  command     => 'systemctl daemon-reload',
  path        => '/usr/bin:/bin',
  refreshonly => true,
}
